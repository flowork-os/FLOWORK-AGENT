// [FL_INDEX: keywords="hybrid_search, rrf, tantivy, vector, graph_expansion, embedder, persistent_writer" | purpose="Tri-Engine Hybrid Fusion layer combining Tantivy FTS, PQ Vector, and CSR Graph with RRF, persistent writer, and mmap support"]

use std::collections::HashMap;
use std::fs;
use std::io;
use std::path::Path;
use tantivy::collector::TopDocs;
use tantivy::query::QueryParser;
use tantivy::schema::*;
use tantivy::{doc, Index, IndexWriter, ReloadPolicy, TantivyDocument};

use crate::csr::CsrGraph;
use crate::embedder::{FastMicroEmbedder, TextEmbedder};
use crate::vector_pq::{PqCodebook, PqVectorStorage, DIMS};

pub struct HybridSearchEngine {
    index: Index,
    index_writer: Option<IndexWriter>,
    title_field: Field,
    body_field: Field,
    doc_id_field: Field,
    codebook: PqCodebook,
    vector_storage: PqVectorStorage,
    graph: CsrGraph,
    embedder: Box<dyn TextEmbedder>,
    pending_uncommitted: usize,
}

#[derive(Debug, Clone)]
pub struct SearchHit {
    pub doc_id: u32,
    pub rrf_score: f32,
    pub title: String,
    pub graph_neighbors: Vec<u32>,
}

impl HybridSearchEngine {
    pub fn new<P: AsRef<Path>>(index_path: P, num_nodes: usize) -> tantivy::Result<Self> {
        let index_path = index_path.as_ref();
        fs::create_dir_all(index_path)?;

        let mut schema_builder = Schema::builder();
        let doc_id_field = schema_builder.add_u64_field("doc_id", INDEXED | STORED | FAST);
        let title_field = schema_builder.add_text_field("title", TEXT | STORED);
        let body_field = schema_builder.add_text_field("body", TEXT);
        let schema = schema_builder.build();

        let index = Index::create_in_dir(index_path, schema)?;

        Ok(Self {
            index,
            index_writer: None,
            title_field,
            body_field,
            doc_id_field,
            codebook: PqCodebook::dummy_or_train(),
            vector_storage: PqVectorStorage::new(),
            graph: CsrGraph::new(num_nodes),
            embedder: Box::new(FastMicroEmbedder::new()),
            pending_uncommitted: 0,
        })
    }

    pub fn set_embedder<E: TextEmbedder + 'static>(&mut self, embedder: E) {
        self.embedder = Box::new(embedder);
    }

    pub fn set_graph(&mut self, graph: CsrGraph) {
        self.graph = graph;
    }

    pub fn set_codebook(&mut self, codebook: PqCodebook) {
        self.codebook = codebook;
    }

    fn ensure_writer(&mut self) -> tantivy::Result<&mut IndexWriter> {
        if self.index_writer.is_none() {
            let writer = self.index.writer(60_000_000)?;
            self.index_writer = Some(writer);
        }
        Ok(self.index_writer.as_mut().unwrap())
    }

    pub fn commit(&mut self) -> tantivy::Result<()> {
        if let Some(ref mut writer) = self.index_writer {
            writer.commit()?;
            self.pending_uncommitted = 0;
        }
        Ok(())
    }

    pub fn insert_document(
        &mut self,
        doc_id: u32,
        title: &str,
        body: &str,
        embedding: Option<&[f32]>,
    ) -> tantivy::Result<()> {
        let doc_id_field = self.doc_id_field;
        let title_field = self.title_field;
        let body_field = self.body_field;

        {
            let writer = self.ensure_writer()?;
            writer.add_document(doc!(
                doc_id_field => doc_id as u64,
                title_field => title,
                body_field => body,
            ))?;
        }

        self.pending_uncommitted = self.pending_uncommitted.saturating_add(1);
        if self.pending_uncommitted >= 5_000 {
            self.commit()?;
        }

        // Use custom embedding if provided, otherwise compute via built-in embedder
        let pq_code = match embedding {
            Some(emb) if emb.len() == DIMS => self.codebook.encode(emb),
            _ => {
                let text_repr = format!("{} {}", title, body);
                let generated_emb = self.embedder.embed(&text_repr);
                self.codebook.encode(&generated_emb)
            }
        };

        self.vector_storage.add(&pq_code);
        Ok(())
    }

    pub fn index_batch(
        &mut self,
        batch: Vec<(u32, &str, &str, Option<&[f32]>)>,
    ) -> tantivy::Result<()> {
        let doc_id_field = self.doc_id_field;
        let title_field = self.title_field;
        let body_field = self.body_field;

        {
            let writer = self.ensure_writer()?;
            for (doc_id, title, body, _) in &batch {
                writer.add_document(doc!(
                    doc_id_field => *doc_id as u64,
                    title_field => *title,
                    body_field => *body,
                ))?;
            }
        }

        for (_doc_id, title, body, embedding) in batch {
            let pq_code = match embedding {
                Some(emb) if emb.len() == DIMS => self.codebook.encode(emb),
                _ => {
                    let text_repr = format!("{} {}", title, body);
                    let generated_emb = self.embedder.embed(&text_repr);
                    self.codebook.encode(&generated_emb)
                }
            };
            self.vector_storage.add(&pq_code);
        }

        self.commit()?;
        Ok(())
    }

    pub fn save_state<P: AsRef<Path>>(&self, dir: P) -> io::Result<()> {
        let dir = dir.as_ref();
        fs::create_dir_all(dir)?;

        self.graph.save_to_disk(dir.join("graph"))?;
        self.codebook.save_to_disk(dir.join("codebook.bin"))?;
        self.vector_storage.save_to_disk(dir.join("vectors.pq"))?;
        Ok(())
    }

    pub fn load_state<P: AsRef<Path>>(dir: P, index_dir: P) -> tantivy::Result<Self> {
        let dir = dir.as_ref();
        let index_dir = index_dir.as_ref();

        let graph = CsrGraph::load_from_disk(dir.join("graph"))
            .map_err(|e| tantivy::TantivyError::InternalError(format!("Failed to load graph: {}", e)))?;
        let codebook = PqCodebook::load_from_disk(dir.join("codebook.bin"))
            .map_err(|e| tantivy::TantivyError::InternalError(format!("Failed to load codebook: {}", e)))?;
        let vector_storage = PqVectorStorage::load_from_mmap(dir.join("vectors.pq"))
            .map_err(|e| tantivy::TantivyError::InternalError(format!("Failed to mmap vectors: {}", e)))?;

        let index = Index::open_in_dir(index_dir)?;
        let schema = index.schema();
        let doc_id_field = schema.get_field("doc_id").unwrap();
        let title_field = schema.get_field("title").unwrap();
        let body_field = schema.get_field("body").unwrap();

        Ok(Self {
            index,
            index_writer: None,
            title_field,
            body_field,
            doc_id_field,
            codebook,
            vector_storage,
            graph,
            embedder: Box::new(FastMicroEmbedder::new()),
            pending_uncommitted: 0,
        })
    }

    pub fn vector_storage_size_bytes(&self) -> usize {
        self.vector_storage.size_bytes()
    }

    /// Primary search interface: automatically generates embedding from text query
    pub fn search(&self, text_query: &str, top_k: usize) -> tantivy::Result<Vec<SearchHit>> {
        let query_vec = self.embedder.embed(text_query);
        self.hybrid_search(text_query, &query_vec, top_k)
    }

    pub fn hybrid_search(
        &self,
        text_query: &str,
        query_vector: &[f32],
        top_k: usize,
    ) -> tantivy::Result<Vec<SearchHit>> {
        const RRF_K: f32 = 60.0;
        let mut rrf_scores: HashMap<u32, f32> = HashMap::new();

        // 1. Tantivy Full-Text Search
        let reader = self
            .index
            .reader_builder()
            .reload_policy(ReloadPolicy::OnCommitWithDelay)
            .try_into()?;
        let searcher = reader.searcher();
        let query_parser = QueryParser::for_index(&self.index, vec![self.title_field, self.body_field]);
        
        if let Ok(parsed_query) = query_parser.parse_query(text_query) {
            let top_docs = searcher.search(&parsed_query, &TopDocs::with_limit(top_k * 2))?;
            for (rank, (_score, doc_address)) in top_docs.into_iter().enumerate() {
                let retrieved_doc: TantivyDocument = searcher.doc(doc_address)?;
                if let Some(doc_id_val) = retrieved_doc.get_first(self.doc_id_field) {
                    if let Some(id_u64) = doc_id_val.as_u64() {
                        let id = id_u64 as u32;
                        let rrf_weight = 1.0 / (RRF_K + (rank as f32) + 1.0);
                        *rrf_scores.entry(id).or_insert(0.0) += rrf_weight;
                    }
                }
            }
        }

        // 2. Vector PQ Search with Relevance Gating using parallel bounded heaps
        if query_vector.len() == DIMS {
            let dist_table = self.codebook.compute_distance_table(query_vector);
            let vec_results = self.vector_storage.scan_top_k(&dist_table, top_k * 4);
            
            const MAX_DISTANCE_GATE: f32 = 85.0;

            let mut rank: usize = 0;
            for (doc_id, dist) in vec_results {
                let has_fts_match = rrf_scores.contains_key(&doc_id);
                if dist <= MAX_DISTANCE_GATE || has_fts_match {
                    let rrf_weight = 1.0 / (RRF_K + (rank as f32) + 1.0);
                    *rrf_scores.entry(doc_id).or_insert(0.0) += rrf_weight;
                    rank = rank.saturating_add(1);
                    if rank >= top_k * 2 {
                        break;
                    }
                }
            }
        }

        // 3. Sort by RRF score descending
        let mut ranked: Vec<(u32, f32)> = rrf_scores.into_iter().collect();
        ranked.sort_by(|a, b| b.1.partial_cmp(&a.1).unwrap_or(std::cmp::Ordering::Equal));
        ranked.truncate(top_k);

        // 4. Graph expansion (1-hop & multi-hop entity context linkage)
        let mut final_hits = Vec::new();
        for (doc_id, score) in ranked {
            let mut neighbors = self.graph.get_neighbors(doc_id).to_vec();
            if neighbors.len() <= 2 {
                let mut hop2_neighbors = Vec::new();
                for &n1 in &neighbors {
                    for &n2 in self.graph.get_neighbors(n1) {
                        if n2 != doc_id && !neighbors.contains(&n2) && !hop2_neighbors.contains(&n2) {
                            hop2_neighbors.push(n2);
                        }
                    }
                }
                neighbors.extend(hop2_neighbors);
            }

            final_hits.push(SearchHit {
                doc_id,
                rrf_score: score,
                title: format!("Document #{}", doc_id),
                graph_neighbors: neighbors,
            });
        }

        Ok(final_hits)
    }
}
