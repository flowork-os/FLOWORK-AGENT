// [FL_INDEX: keywords="semantic_embedder, hash_embedding, wordpiece, fast_vector, ngram" | purpose="Zero-dependency lightweight deterministic semantic embedder generating 384-dimensional normalized vectors"]

use crate::vector_pq::DIMS;

/// Trait defining text-to-vector embedding contract
pub trait TextEmbedder: Send + Sync {
    /// Generate normalized 384-dimensional vector embedding from text
    fn embed(&self, text: &str) -> [f32; DIMS];
}

/// Lightweight deterministic subword-ngram semantic embedder
/// Employs subword-weighted feature projection with L2 unit normalization,
/// simulating character-level typo tolerance and semantic clustering.
#[derive(Clone, Default)]
pub struct FastMicroEmbedder;

impl FastMicroEmbedder {
    pub fn new() -> Self {
        Self
    }
}

impl TextEmbedder for FastMicroEmbedder {
    fn embed(&self, text: &str) -> [f32; DIMS] {
        let mut vec = [0.0f32; DIMS];
        let lower = text.to_lowercase();
        let tokens: Vec<&str> = lower.split_whitespace().collect();

        if tokens.is_empty() {
            return vec;
        }

        for (t_idx, token) in tokens.iter().enumerate() {
            let bytes = token.as_bytes();
            let len = bytes.len();

            // Positional decay weight
            let pos_weight = 1.0 + (1.0 / ((t_idx + 1) as f32).sqrt());

            // 1. Whole token hash projection (light weight)
            let token_hash = fnv1a_hash(bytes);
            let slot = (token_hash as usize) % DIMS;
            vec[slot] += 0.5 * pos_weight;

            // 2. Character 2-grams, 3-grams, and 4-grams subwords (dominant weight for fuzzy/typo robustness)
            if len >= 2 {
                for i in 0..=len - 2 {
                    let sub_hash = fnv1a_hash(&bytes[i..i + 2]);
                    let sub_slot = (sub_hash as usize) % DIMS;
                    vec[sub_slot] += 0.6 * pos_weight;
                }
            }
            if len >= 3 {
                for i in 0..=len - 3 {
                    let sub_hash = fnv1a_hash(&bytes[i..i + 3]);
                    let sub_slot = (sub_hash as usize) % DIMS;
                    vec[sub_slot] += 1.0 * pos_weight;
                }
            }
            if len >= 4 {
                for i in 0..=len - 4 {
                    let sub_hash = fnv1a_hash(&bytes[i..i + 4]);
                    let sub_slot = (sub_hash as usize) % DIMS;
                    vec[sub_slot] += 0.8 * pos_weight;
                }
            }
        }

        // L2 Unit Normalization (Euclidean norm)
        let norm_sq: f32 = vec.iter().map(|v| v * v).sum();
        if norm_sq > 0.0 {
            let inv_norm = 1.0 / norm_sq.sqrt();
            for v in vec.iter_mut() {
                *v *= inv_norm;
            }
        }

        vec
    }
}

/// 64-bit FNV-1a Hash Algorithm
#[inline(always)]
fn fnv1a_hash(data: &[u8]) -> u64 {
    const FNV_OFFSET_BASIS: u64 = 0xcbf29ce484222325;
    const FNV_PRIME: u64 = 0x100000001b3;

    let mut hash = FNV_OFFSET_BASIS;
    for &byte in data {
        hash ^= byte as u64;
        hash = hash.wrapping_mul(FNV_PRIME);
    }
    hash
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_micro_embedder_normalization() {
        let embedder = FastMicroEmbedder::new();
        let vec = embedder.embed("optimasi query database sql postgresql");
        assert_eq!(vec.len(), DIMS);

        let norm: f32 = vec.iter().map(|v| v * v).sum();
        assert!((norm.sqrt() - 1.0).abs() < 1e-4);
    }

    #[test]
    fn test_subword_semantic_similarity() {
        let embedder = FastMicroEmbedder::new();
        let vec_orig = embedder.embed("database optimization");
        let vec_typo = embedder.embed("database optimizaton"); // typo tolerance

        let dot_product: f32 = vec_orig.iter().zip(vec_typo.iter()).map(|(a, b)| a * b).sum();
        assert!(dot_product > 0.80, "Typo should maintain high cosine similarity: {}", dot_product);
    }
}
