// [FL_INDEX: keywords="rust, semantic_search, fastembed, onnx, cli" | purpose="Sovereign CLI engine for semantic search over local workspace files"]

use std::fs;
use std::path::{Path, PathBuf};
use anyhow::{Context, Result};
use clap::Parser;
use fastembed::{EmbeddingModel, InitOptions, TextEmbedding};
use serde::{Deserialize, Serialize};
use walkdir::WalkDir;

#[derive(Parser, Debug)]
#[command(author = "Flowork OS", version = "0.1.0", about = "Sovereign FastEmbed Semantic Search Engine")]
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

    /// Optional explicit cache directory for models
    #[arg(long)]
    cache_dir: Option<String>,

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

struct IndexedDoc {
    path: String,
    title: String,
    snippet: String,
    content_chunk: String,
    recency_rank: usize,
    total_steps: usize,
    is_chat: bool,
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

    // Dynamic resolution relative to current working directory
    let default_portable = PathBuf::from("portable-home").join(".flowork").join("models");
    default_portable
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
        .filter(|l| !l.is_empty() && !l.starts_with("#") && !l.starts_with("//") && !l.starts_with("<!--"))
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

fn parse_jsonl_transcript(path: &Path) -> Vec<IndexedDoc> {
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

            docs.push(IndexedDoc {
                path: format!("{}:turn_{}", path.display(), idx + 1),
                title,
                snippet,
                content_chunk: truncated_chunk,
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

    let mut indexed_files: Vec<IndexedDoc> = Vec::new();

    for entry in WalkDir::new(target_dir).into_iter().filter_map(|e| e.ok()) {
        let path = entry.path();
        if path.is_file() {
            let ext = path.extension().and_then(|s| s.to_str()).unwrap_or("");
            if matches!(ext, "md" | "json" | "jsonl" | "txt" | "rs" | "js" | "mjs" | "ts") {
                if let Ok(content) = fs::read_to_string(path) {
                    if content.trim().is_empty() {
                        continue;
                    }
                    let file_name = path.file_name().and_then(|s| s.to_str()).unwrap_or("file");
                    let (title, snippet) = extract_title_and_snippet(&content, file_name);

                    // Truncate document text to 1000 characters for semantic embedding
                    let truncated_text: String = content.chars().take(1000).collect();
                    indexed_files.push(IndexedDoc {
                        path: path.display().to_string(),
                        title,
                        snippet,
                        content_chunk: truncated_text,
                        recency_rank: 0,
                        total_steps: 0,
                        is_chat: false,
                    });
                }
            }
        }
    }

    if args.include_chat {
        let chat_sessions_dir = PathBuf::from("portable-home").join(".flowork").join("chat_sessions");
        if chat_sessions_dir.exists() {
            for entry in WalkDir::new(&chat_sessions_dir).into_iter().filter_map(|e| e.ok()) {
                let path = entry.path();
                if path.is_file() && path.extension().and_then(|s| s.to_str()) == Some("jsonl") {
                    let mut chat_docs = parse_jsonl_transcript(path);
                    indexed_files.append(&mut chat_docs);
                }
            }
        }
    }

    if indexed_files.is_empty() {
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

    let doc_texts: Vec<&str> = indexed_files.iter().map(|d| d.content_chunk.as_str()).collect();
    let doc_embeddings = model
        .embed(doc_texts, None)
        .context("Failed to embed document chunks")?;

    let mut scored_results: Vec<SearchResult> = Vec::new();

    for (i, doc_vector) in doc_embeddings.into_iter().enumerate() {
        let base_score = cosine_similarity(query_vector, &doc_vector);
        let doc = &indexed_files[i];

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

        scored_results.push(SearchResult {
            file_path: doc.path.clone(),
            score: (final_score * 1000.0).round() / 1000.0,
            base_semantic_score: (base_score * 1000.0).round() / 1000.0,
            recency_factor: (recency_factor * 1000.0).round() / 1000.0,
            title: doc.title.clone(),
            snippet: doc.snippet.clone(),
        });
    }

    scored_results.sort_by(|a, b| b.score.partial_cmp(&a.score).unwrap_or(std::cmp::Ordering::Equal));
    scored_results.truncate(args.top_k);

    let json_output = serde_json::to_string_pretty(&scored_results)
        .context("Failed to serialize results to JSON")?;
    println!("{}", json_output);

    Ok(())
}
