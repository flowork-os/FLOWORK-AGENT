// [FL_INDEX: keywords="rust, semantic_search, fastembed, onnx, cli, vector_cache, zero_noise" | purpose="Sovereign High-Performance Cached Semantic Search Engine"]

use std::collections::HashMap;
use std::fs;
use std::path::{Path, PathBuf};
use std::time::UNIX_EPOCH;
use anyhow::{Context, Result};
use clap::Parser;
use fastembed::{EmbeddingModel, InitOptions, TextEmbedding};
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use walkdir::WalkDir;

#[derive(Parser, Debug)]
#[command(author = "Flowork OS", version = "0.2.0", about = "Sovereign Cached FastEmbed Semantic Search Engine")]
struct Args {
    /// Semantic search query
    #[arg(short, long)]
    query: String,

    /// Target directory to scan/index
    #[arg(short, long, default_value = ".fl_brain")]
    target: String,

    /// Model to use: bge-small or all-minilm (defaults to bge-small)
    #[arg(short, long, default_value = "bge-small")]
    model: String,

    /// Max results to return
    #[arg(short = 'k', long, default_value_t = 5)]
    top_k: usize,

    /// Minimum semantic similarity score threshold (default: 0.50)
    #[arg(short = 's', long, default_value_t = 0.50)]
    min_score: f32,

    /// Optional explicit cache directory for models
    #[arg(long)]
    cache_dir: Option<String>,

    /// Force clear and rebuild vector cache
    #[arg(long, default_value_t = false)]
    rebuild_cache: bool,

    /// Include chat sessions from portable-home/.flowork/chat_sessions
    #[arg(long, default_value_t = false)]
    include_chat: bool,

    /// Recency decay half-life in turns (default: 50.0 turns)
    #[arg(long, default_value_t = 50.0)]
    recency_decay: f32,
}

#[derive(Serialize, Deserialize, Debug)]
struct SearchResult {
    file_path: String,
    score: f32,
    base_semantic_score: f32,
    recency_factor: f32,
    title: String,
    snippet: String,
}

#[derive(Serialize, Deserialize, Clone, Debug)]
struct CachedEntry {
    sha256: String,
    mtime: u64,
    title: String,
    snippet: String,
    vector: Vec<f32>,
}

#[derive(Serialize, Deserialize, Default, Debug)]
struct VectorCacheStore {
    version: String,
    model: String,
    entries: HashMap<String, CachedEntry>,
}

struct ReadyDoc {
    path: String,
    title: String,
    snippet: String,
    vector: Vec<f32>,
    recency_rank: usize,
    total_steps: usize,
    is_chat: bool,
}

struct UncachedDoc {
    path: String,
    title: String,
    snippet: String,
    content_chunk: String,
    sha256: String,
    mtime: u64,
    recency_rank: usize,
    total_steps: usize,
    is_chat: bool,
}

fn compute_sha256(data: &[u8]) -> String {
    let mut hasher = Sha256::new();
    hasher.update(data);
    format!("{:x}", hasher.finalize())
}

fn resolve_cache_dir(explicit: Option<String>) -> PathBuf {
    if let Some(dir) = explicit {
        return PathBuf::from(dir);
    }

    if let Ok(portable_root) = std::env::var("FLOWORK_PORTABLE_ROOT") {
        if !portable_root.trim().is_empty() {
            return PathBuf::from(portable_root).join(".flowork").join("models");
        }
    }

    PathBuf::from("portable-home").join(".flowork").join("models")
}

fn resolve_vector_cache_file() -> PathBuf {
    if let Ok(portable_root) = std::env::var("FLOWORK_PORTABLE_ROOT") {
        if !portable_root.trim().is_empty() {
            return PathBuf::from(portable_root).join(".flowork").join("semantic_vector_cache.json");
        }
    }
    let p = PathBuf::from("portable-home").join(".flowork");
    if p.exists() {
        return p.join("semantic_vector_cache.json");
    }
    let dot_fl = PathBuf::from(".flowork");
    if dot_fl.exists() {
        return dot_fl.join("semantic_vector_cache.json");
    }
    PathBuf::from("semantic_vector_cache.json")
}

fn cosine_similarity(a: &[f32], b: &[f32]) -> f32 {
    let dot: f32 = a.iter().zip(b.iter()).map(|(x, y)| x * y).sum();
    let norm_a: f32 = a.iter().map(|x| x * x).sum::<f32>().sqrt();
    let norm_b: f32 = b.iter().map(|x| x * x).sum::<f32>().sqrt();
    if norm_a == 0.0 || norm_b == 0.0 {
        0.0
    } else {
        dot / (norm_a * norm_b)
    }
}

fn extract_title_and_snippet(content: &str, file_name: &str) -> (String, String) {
    let lines: Vec<&str> = content.lines().collect();
    let mut title = file_name.to_string();

    for line in &lines {
        let trimmed = line.trim();
        if trimmed.starts_with("# ") {
            title = trimmed.trim_start_matches("# ").trim().to_string();
            break;
        } else if trimmed.starts_with("title:") {
            title = trimmed.trim_start_matches("title:").trim().trim_matches('"').to_string();
            break;
        }
    }

    let non_empty: Vec<&str> = lines
        .into_iter()
        .map(|l| l.trim())
        .filter(|l| !l.is_empty() && !l.starts_with('#') && !l.starts_with("//") && !l.starts_with("<!--"))
        .collect();

    let snippet = if non_empty.is_empty() {
        content.chars().take(200).collect::<String>()
    } else {
        let combined = non_empty.join(" ");
        if combined.chars().count() > 240 {
            let truncated: String = combined.chars().take(240).collect();
            format!("{}...", truncated)
        } else {
            combined
        }
    };

    (title, snippet)
}

fn is_blacklisted_path(path: &Path) -> bool {
    let path_str = path.to_string_lossy();
    let lower = path_str.to_lowercase();

    // Check directory blacklist
    if lower.contains("/target/") 
        || lower.contains("/node_modules/") 
        || lower.contains("/.git/") 
        || lower.contains("/.cargo/") 
        || lower.contains("/.flowork_spam/") 
        || lower.contains("/.fl_spam/")
        || lower.contains("/scratch/") 
        || lower.contains("/archived_incidents/")
        || lower.contains("/file_histories/") 
        || lower.contains("/browser-profile/")
        || lower.contains("/.system_generated/") {
        return true;
    }

    // Check file name blacklist
    if let Some(file_name) = path.file_name().and_then(|s| s.to_str()) {
        let fn_lower = file_name.to_lowercase();
        if fn_lower.starts_with("activity_") 
            || fn_lower.contains("activity_part")
            || fn_lower.ends_with(".jsonl") 
            || fn_lower.ends_with(".log") 
            || fn_lower.ends_with(".tmp")
            || fn_lower.ends_with(".bak")
            || fn_lower.ends_with(".lock") {
            return true;
        }
    }

    false
}

fn is_valid_document_extension(path: &Path, is_brain_target: bool) -> bool {
    let ext = path.extension().and_then(|s| s.to_str()).unwrap_or("");
    if is_brain_target {
        // Kubah Ingatan: Atomic 1 file 1 solution, strictly Markdown
        matches!(ext, "md")
    } else {
        // Workspace general: Markdown, docs, config, source code
        matches!(ext, "md" | "txt" | "rs" | "js" | "mjs" | "ts" | "py" | "sh" | "toml" | "json")
    }
}

fn parse_jsonl_transcript(path: &Path) -> Vec<UncachedDoc> {
    let mut docs = Vec::new();
    let content = match fs::read_to_string(path) {
        Ok(c) => c,
        Err(_) => return docs,
    };

    let lines: Vec<&str> = content.lines().filter(|l| !l.trim().is_empty()).collect();
    let total_lines = lines.len();
    if total_lines == 0 {
        return docs;
    }

    for (idx, line) in lines.iter().enumerate() {
        if let Ok(v) = serde_json::from_str::<serde_json::Value>(line) {
            let role = v.get("role").and_then(|s| s.as_str()).unwrap_or("unknown");
            let mut text_acc = String::new();

            if let Some(content_val) = v.get("content") {
                if let Some(s) = content_val.as_str() {
                    text_acc.push_str(s);
                } else if let Some(arr) = content_val.as_array() {
                    for part in arr {
                        if let Some(text) = part.get("text").and_then(|t| t.as_str()) {
                            text_acc.push_str(text);
                            text_acc.push(' ');
                        }
                    }
                }
            }

            if text_acc.trim().is_empty() {
                continue;
            }

            let cleaned = text_acc.trim();
            let snippet: String = cleaned.chars().take(240).collect();
            let title = format!("Chat [{}] Turn #{} of {}", role, idx + 1, total_lines);
            let truncated_chunk: String = cleaned.chars().take(1000).collect();
            let chunk_sha256 = compute_sha256(truncated_chunk.as_bytes());

            docs.push(UncachedDoc {
                path: format!("{}:turn_{}", path.display(), idx + 1),
                title,
                snippet,
                content_chunk: truncated_chunk,
                sha256: chunk_sha256,
                mtime: 0,
                recency_rank: idx + 1,
                total_steps: total_lines,
                is_chat: true,
            });
        }
    }

    docs
}

fn main() -> Result<()> {
    let args = Args::parse();

    let cache_dir = resolve_cache_dir(args.cache_dir);
    if !cache_dir.exists() {
        fs::create_dir_all(&cache_dir).context("Failed to create portable models cache directory")?;
    }

    let selected_model = match args.model.to_lowercase().as_str() {
        "all-minilm" | "minilm" => EmbeddingModel::AllMiniLML6V2,
        _ => EmbeddingModel::BGESmallENV15,
    };

    let model = TextEmbedding::try_new(
        InitOptions::new(selected_model)
            .with_cache_dir(cache_dir)
            .with_show_download_progress(false),
    ).context("Failed to initialize FastEmbed model")?;

    let target_dir = Path::new(&args.target);
    if !target_dir.exists() {
        println!("[]");
        return Ok(());
    }

    let vector_cache_file = resolve_vector_cache_file();
    let mut cache_store: VectorCacheStore = if !args.rebuild_cache && vector_cache_file.exists() {
        fs::read_to_string(&vector_cache_file)
            .ok()
            .and_then(|c| serde_json::from_str::<VectorCacheStore>(&c).ok())
            .filter(|s| s.model == args.model)
            .unwrap_or_else(|| VectorCacheStore {
                version: "1.0".to_string(),
                model: args.model.clone(),
                entries: HashMap::new(),
            })
    } else {
        VectorCacheStore {
            version: "1.0".to_string(),
            model: args.model.clone(),
            entries: HashMap::new(),
        }
    };

    let mut ready_docs: Vec<ReadyDoc> = Vec::new();
    let mut uncached_docs: Vec<UncachedDoc> = Vec::new();

    let is_brain_target = target_dir.to_string_lossy().contains(".fl_brain");

    for entry in WalkDir::new(target_dir).into_iter().filter_map(|e| e.ok()) {
        let path = entry.path();
        if !path.is_file() {
            continue;
        }

        if is_blacklisted_path(path) {
            continue;
        }

        if !is_valid_document_extension(path, is_brain_target) {
            continue;
        }

        let mtime = fs::metadata(path)
            .and_then(|m| m.modified())
            .ok()
            .and_then(|t| t.duration_since(UNIX_EPOCH).ok())
            .map(|d| d.as_secs())
            .unwrap_or(0);

        let content = match fs::read_to_string(path) {
            Ok(c) => c,
            Err(_) => continue,
        };

        if content.trim().is_empty() {
            continue;
        }

        let sha256 = compute_sha256(content.as_bytes());
        let path_key = path.display().to_string();

        if let Some(cached) = cache_store.entries.get(&path_key) {
            if cached.sha256 == sha256 {
                ready_docs.push(ReadyDoc {
                    path: path_key,
                    title: cached.title.clone(),
                    snippet: cached.snippet.clone(),
                    vector: cached.vector.clone(),
                    recency_rank: 0,
                    total_steps: 0,
                    is_chat: false,
                });
                continue;
            }
        }

        let file_name = path.file_name().and_then(|s| s.to_str()).unwrap_or("file");
        let (title, snippet) = extract_title_and_snippet(&content, file_name);
        let truncated_text: String = content.chars().take(1000).collect();

        uncached_docs.push(UncachedDoc {
            path: path_key,
            title,
            snippet,
            content_chunk: truncated_text,
            sha256,
            mtime,
            recency_rank: 0,
            total_steps: 0,
            is_chat: false,
        });
    }

    if args.include_chat {
        let chat_sessions_dir = PathBuf::from("portable-home").join(".flowork").join("chat_sessions");
        if chat_sessions_dir.exists() {
            for entry in WalkDir::new(&chat_sessions_dir).into_iter().filter_map(|e| e.ok()) {
                let path = entry.path();
                if path.is_file() && path.extension().and_then(|s| s.to_str()) == Some("jsonl") {
                    let chat_docs = parse_jsonl_transcript(path);
                    for cdoc in chat_docs {
                        if let Some(cached) = cache_store.entries.get(&cdoc.path) {
                            if cached.sha256 == cdoc.sha256 {
                                ready_docs.push(ReadyDoc {
                                    path: cdoc.path,
                                    title: cached.title.clone(),
                                    snippet: cached.snippet.clone(),
                                    vector: cached.vector.clone(),
                                    recency_rank: cdoc.recency_rank,
                                    total_steps: cdoc.total_steps,
                                    is_chat: true,
                                });
                                continue;
                            }
                        }
                        uncached_docs.push(cdoc);
                    }
                }
            }
        }
    }

    if !uncached_docs.is_empty() {
        let dirty_texts: Vec<&str> = uncached_docs.iter().map(|d| d.content_chunk.as_str()).collect();
        let dirty_embeddings = model
            .embed(dirty_texts, None)
            .context("Failed to embed new or modified documents")?;

        for (doc, vector) in uncached_docs.into_iter().zip(dirty_embeddings.into_iter()) {
            cache_store.entries.insert(
                doc.path.clone(),
                CachedEntry {
                    sha256: doc.sha256,
                    mtime: doc.mtime,
                    title: doc.title.clone(),
                    snippet: doc.snippet.clone(),
                    vector: vector.clone(),
                },
            );

            ready_docs.push(ReadyDoc {
                path: doc.path,
                title: doc.title,
                snippet: doc.snippet,
                vector,
                recency_rank: doc.recency_rank,
                total_steps: doc.total_steps,
                is_chat: doc.is_chat,
            });
        }

        // Persist vector cache to disk
        if let Some(parent) = vector_cache_file.parent() {
            let _ = fs::create_dir_all(parent);
        }
        if let Ok(serialized) = serde_json::to_string(&cache_store) {
            let _ = fs::write(&vector_cache_file, serialized);
        }
    }

    if ready_docs.is_empty() {
        println!("[]");
        return Ok(());
    }

    let query_embeddings = model
        .embed(vec![&args.query], None)
        .context("Failed to embed search query")?;
    let query_vector = match query_embeddings.first() {
        Some(v) => v,
        None => {
            println!("[]");
            return Ok(());
        }
    };

    let mut scored_results: Vec<SearchResult> = Vec::new();

    for doc in ready_docs {
        let base_score = cosine_similarity(query_vector, &doc.vector);

        let recency_factor = if doc.is_chat && doc.total_steps > 0 {
            let distance_from_latest = (doc.total_steps - doc.recency_rank) as f32;
            let decay_lambda = 0.69315 / args.recency_decay.max(1.0);
            (-decay_lambda * distance_from_latest).exp()
        } else {
            1.0
        };

        // Recency-weighted blend: 65% base semantic relevance + 35% recency multiplier for chat
        let final_score = if doc.is_chat {
            base_score * (0.65 + 0.35 * recency_factor)
        } else {
            base_score
        };

        // Minimum threshold guard to filter out semantic noise
        if final_score < args.min_score {
            continue;
        }

        scored_results.push(SearchResult {
            file_path: doc.path,
            score: (final_score * 1000.0).round() / 1000.0,
            base_semantic_score: (base_score * 1000.0).round() / 1000.0,
            recency_factor: (recency_factor * 1000.0).round() / 1000.0,
            title: doc.title,
            snippet: doc.snippet,
        });
    }

    scored_results.sort_by(|a, b| b.score.partial_cmp(&a.score).unwrap_or(std::cmp::Ordering::Equal));
    scored_results.truncate(args.top_k);

    let json_output = serde_json::to_string_pretty(&scored_results)
        .context("Failed to serialize results to JSON")?;
    println!("{}", json_output);

    Ok(())
}
