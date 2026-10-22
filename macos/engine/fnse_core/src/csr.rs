// [FL_INDEX: keywords="csr, graph, sparse_row, zero_copy, mmap" | purpose="Compressed Sparse Row binary graph engine for O(1) neighbor lookups"]

use std::fs::File;
use std::io::{self, BufWriter, Write};
use std::path::Path;

#[derive(Debug)]
pub struct CsrGraph {
    offsets: Vec<u32>,
    edges: Vec<u32>,
}

impl CsrGraph {
    pub fn new(num_nodes: usize) -> Self {
        Self {
            offsets: vec![0; num_nodes.saturating_add(1)],
            edges: Vec::new(),
        }
    }

    pub fn from_adjacency_list(adj: &[Vec<u32>]) -> Self {
        let num_nodes = adj.len();
        let mut offsets = Vec::with_capacity(num_nodes.saturating_add(1));
        let total_edges: usize = adj.iter().map(|v| v.len()).sum();
        let mut edges = Vec::with_capacity(total_edges);

        let mut current_offset: u32 = 0;
        offsets.push(current_offset);

        for neighbors in adj {
            for &target in neighbors {
                edges.push(target);
            }
            current_offset = current_offset.saturating_add(neighbors.len() as u32);
            offsets.push(current_offset);
        }

        Self { offsets, edges }
    }

    #[inline(always)]
    pub fn get_neighbors(&self, node_id: u32) -> &[u32] {
        let idx = node_id as usize;
        if idx.saturating_add(1) >= self.offsets.len() {
            return &[];
        }
        let start = self.offsets[idx] as usize;
        let end = self.offsets[idx.saturating_add(1)] as usize;
        if start <= end && end <= self.edges.len() {
            &self.edges[start..end]
        } else {
            &[]
        }
    }

    pub fn save_to_disk<P: AsRef<Path>>(&self, dir: P) -> io::Result<()> {
        let dir = dir.as_ref();
        std::fs::create_dir_all(dir)?;

        let offsets_path = dir.join("offsets.bin");
        let edges_path = dir.join("edges.bin");

        let mut off_writer = BufWriter::new(File::create(offsets_path)?);
        for &val in &self.offsets {
            off_writer.write_all(&val.to_le_bytes())?;
        }
        off_writer.flush()?;

        let mut edge_writer = BufWriter::new(File::create(edges_path)?);
        for &val in &self.edges {
            edge_writer.write_all(&val.to_le_bytes())?;
        }
        edge_writer.flush()?;

        Ok(())
    }

    pub fn load_from_disk<P: AsRef<Path>>(dir: P) -> io::Result<Self> {
        let dir = dir.as_ref();
        let offsets_bytes = std::fs::read(dir.join("offsets.bin"))?;
        let edges_bytes = std::fs::read(dir.join("edges.bin"))?;

        if offsets_bytes.len() % 4 != 0 || edges_bytes.len() % 4 != 0 {
            return Err(io::Error::new(io::ErrorKind::InvalidData, "CSR binary alignment mismatch"));
        }

        let offsets: Vec<u32> = offsets_bytes
            .chunks_exact(4)
            .map(|chunk| u32::from_le_bytes([chunk[0], chunk[1], chunk[2], chunk[3]]))
            .collect();

        let edges: Vec<u32> = edges_bytes
            .chunks_exact(4)
            .map(|chunk| u32::from_le_bytes([chunk[0], chunk[1], chunk[2], chunk[3]]))
            .collect();

        Ok(Self { offsets, edges })
    }

    #[inline(always)]
    pub fn num_nodes(&self) -> usize {
        self.offsets.len().saturating_sub(1)
    }

    #[inline(always)]
    pub fn num_edges(&self) -> usize {
        self.edges.len()
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use tempfile::tempdir;

    #[test]
    fn test_csr_roundtrip_and_lookups() {
        let adj = vec![
            vec![1, 2],       // Node 0 -> 1, 2
            vec![2, 3],       // Node 1 -> 2, 3
            vec![0],          // Node 2 -> 0
            vec![],           // Node 3 -> (none)
        ];

        let graph = CsrGraph::from_adjacency_list(&adj);
        assert_eq!(graph.num_nodes(), 4);
        assert_eq!(graph.num_edges(), 5);

        assert_eq!(graph.get_neighbors(0), &[1, 2]);
        assert_eq!(graph.get_neighbors(1), &[2, 3]);
        assert_eq!(graph.get_neighbors(2), &[0]);
        let empty: &[u32] = &[];
        assert_eq!(graph.get_neighbors(3), empty);
        assert_eq!(graph.get_neighbors(99), empty);

        let tmp = tempdir().unwrap();
        graph.save_to_disk(tmp.path()).unwrap();
        let loaded = CsrGraph::load_from_disk(tmp.path()).unwrap();

        assert_eq!(loaded.num_nodes(), 4);
        assert_eq!(loaded.num_edges(), 5);
        assert_eq!(loaded.get_neighbors(1), &[2, 3]);
    }
}
