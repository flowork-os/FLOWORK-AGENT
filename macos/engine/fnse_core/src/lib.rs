// [FL_INDEX: keywords="fnse, tri_engine, fts, vector, graph" | purpose="FNSE core library root exposing CSR graph, Vector PQ, and Hybrid Fusion"]

pub mod csr;
pub mod vector_pq;
pub mod fusion;
pub mod embedder;

pub use csr::CsrGraph;
pub use vector_pq::{PqCodebook, PqVectorStorage, IvfIndex, DIMS};
pub use fusion::{HybridSearchEngine, SearchHit};
pub use embedder::{FastMicroEmbedder, TextEmbedder};
