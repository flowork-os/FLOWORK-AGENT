// [FL_INDEX: keywords="benchmark, ingestion, synthetic_data, throughput, latency, fnse" | purpose="Comprehensive synthetic ingestion and hybrid search performance benchmark for FNSE"]

use std::fs;
use std::time::Instant;
use tempfile::TempDir;

use fnse_core::csr::CsrGraph;
use fnse_core::fusion::HybridSearchEngine;
use fnse_core::vector_pq::DIMS;

fn generate_synthetic_vector(seed: usize) -> Vec<f32> {
    let mut vec = Vec::with_capacity(DIMS);
    for i in 0..DIMS {
        let val = (((seed + i * 17) % 1000) as f32) / 1000.0;
        vec.push(val);
    }
    vec
}

fn main() {
    println!("============================================================");
    println!("🚀 FLOWORK NEURAL-STORAGE ENGINE (FNSE) SYNTHETIC BENCHMARK");
    println!("============================================================");

    let temp_dir = TempDir::new().expect("Failed to create temporary directory for benchmark");
    let index_path = temp_dir.path().join("fnse_benchmark_index");
    fs::create_dir_all(&index_path).unwrap();

    let benchmark_sizes = vec![10_000, 50_000, 100_000];

    for &num_records in &benchmark_sizes {
        println!("\n>>> RUNNING TEST SUITE: {} SYNTHETIC RECORDS <<<", num_records);

        // 1. Synthetic Graph Construction (CSR)
        print!("  • Generating CSR Graph (Adjacency Matrix)... ");
        let t_graph = Instant::now();
        let mut adj: Vec<Vec<u32>> = Vec::with_capacity(num_records);
        for i in 0..num_records {
            let mut neighbors = Vec::new();
            if i > 0 {
                neighbors.push((i - 1) as u32);
            }
            if i + 1 < num_records {
                neighbors.push((i + 1) as u32);
            }
            if (i % 10 == 0) && (i + 5 < num_records) {
                neighbors.push((i + 5) as u32);
            }
            adj.push(neighbors);
        }
        let graph = CsrGraph::from_adjacency_list(&adj);
        let graph_dur = t_graph.elapsed();
        println!("DONE in {:.2?}", graph_dur);
        println!(
            "    - Nodes: {}, Edges: {}, Memory: ~{:.2} MB",
            graph.num_nodes(),
            graph.num_edges(),
            (graph.num_nodes() * 4 + graph.num_edges() * 4) as f64 / (1024.0 * 1024.0)
        );

        // 2. Synthetic Engine Initialization & Ingestion
        let sub_index_path = index_path.join(format!("test_{}", num_records));
        let mut engine = HybridSearchEngine::new(&sub_index_path, num_records)
            .expect("Failed to initialize HybridSearchEngine");
        engine.set_graph(graph);

        println!("  • Ingesting and Indexing {} Documents (FTS + PQ-Vector)...", num_records);
        let t_ingest = Instant::now();
        let batch_size = 5_000;
        let mut current_batch = Vec::with_capacity(batch_size);

        for doc_id in 0..num_records {
            let title = format!("Flowork Document #{}", doc_id);
            let body = format!(
                "This is the synthetic document payload for ID {} containing sovereign neural concepts, distributed graphs, and tantivy full-text index tokens.",
                doc_id
            );
            let embedding = generate_synthetic_vector(doc_id);
            current_batch.push((doc_id as u32, title, body, embedding));

            if current_batch.len() >= batch_size {
                let batch_refs: Vec<(u32, &str, &str, Option<&[f32]>)> = current_batch
                    .iter()
                    .map(|(id, t, b, e)| (*id, t.as_str(), b.as_str(), Some(e.as_slice())))
                    .collect();
                engine.index_batch(batch_refs).expect("Failed to index FTS batch");
                current_batch.clear();
            }
        }

        if !current_batch.is_empty() {
            let batch_refs: Vec<(u32, &str, &str, Option<&[f32]>)> = current_batch
                .iter()
                .map(|(id, t, b, e)| (*id, t.as_str(), b.as_str(), Some(e.as_slice())))
                .collect();
            engine.index_batch(batch_refs).expect("Failed to index remaining batch");
            current_batch.clear();
        }

        let ingest_dur = t_ingest.elapsed();
        let throughput = (num_records as f64) / ingest_dur.as_secs_f64();
        println!("    - Ingestion Finished in {:.2?}", ingest_dur);
        println!("    - Ingestion Throughput: {:.1} docs/sec", throughput);
        println!(
            "    - Vector Storage Size: {:.2} MB (PQ-8 compression: 48 bytes/vector)",
            (engine.vector_storage_size_bytes() as f64) / (1024.0 * 1024.0)
        );

        // 3. Hybrid Search Latency Benchmark (FTS + Vector + Graph RRF)
        println!("  • Benchmarking Hybrid Query Latency (Tantivy + PQ + Graph RRF)...");
        let query_iterations = 200;
        let mut latencies: Vec<f64> = Vec::with_capacity(query_iterations);

        for q_i in 0..query_iterations {
            let query_text = if q_i % 2 == 0 {
                "sovereign neural concepts"
            } else {
                "distributed graphs tantivy"
            };
            let query_vec = generate_synthetic_vector(q_i * 13);

            let t_query = Instant::now();
            let hits = engine.hybrid_search(query_text, &query_vec, 10).expect("Query failed");
            let q_dur = t_query.elapsed();
            assert!(!hits.is_empty(), "Query returned no results");
            latencies.push(q_dur.as_secs_f64() * 1000.0); // Convert to ms
        }

        latencies.sort_by(|a, b| a.partial_cmp(b).unwrap());
        let p50 = latencies[(latencies.len() as f64 * 0.50) as usize];
        let p95 = latencies[(latencies.len() as f64 * 0.95) as usize];
        let p99 = latencies[(latencies.len() as f64 * 0.99) as usize];
        let avg: f64 = latencies.iter().sum::<f64>() / (latencies.len() as f64);

        println!("     Query Performance (over {} runs):", query_iterations);
        println!("       • Avg Latency : {:.3} ms", avg);
        println!("       • P50 Latency : {:.3} ms", p50);
        println!("       • P95 Latency : {:.3} ms", p95);
        println!("       • P99 Latency : {:.3} ms", p99);
    }

    println!("\n============================================================");
    println!("✅ ALL SYNTHETIC BENCHMARKS COMPLETED WITH VERIFIED SUCCESS");
    println!("============================================================");
}
