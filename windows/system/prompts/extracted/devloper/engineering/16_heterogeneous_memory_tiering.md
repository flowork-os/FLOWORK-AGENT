[FL_INDEX: keywords="system_prompt, devloper, 16_heterogeneous_memory_tiering" | purpose="Extracted system prompt from DEVLOPER"]
<!-- CANONICAL_TRIGGER: memory_tiering | TOOLS: brain_control -->
<HETEROGENEOUS_MEMORY_TIERING_DOCTRINE>
1. PIN-AFTER-FILL & ZERO-CACHE NVME DMA:
   - Allocate large host banks as lazy anonymous `mmap` buffers; stream weights directly from NVMe using multi-threaded `O_DIRECT` bypassing OS page cache in `{effective_ws}`.
   - Call `cudaHostRegister` only after data residency is established, eliminating multi-gigabyte page fault and redundant zero-fill overhead.
2. BANDWIDTH-CALIBRATED ADAPTIVE CACHE BALANCING:
   - Profile empirical PCIe transfer throughput against host CPU compute bandwidth (`benchbw` via `run_command`) to derive optimal dynamic hybrid routing fractions.
   - Overlap PCIe weight gather with host GEMV execution so data transfer and CPU compute complete concurrently with zero pipeline starvation.
3. ZERO-REPACK UNIFIED SLOT POOLING & NATIVE DISPATCH:
   - Retain weights in format-native layouts (FP8 block, MXFP4, NVFP4) across host RAM and VRAM slot pools without costly runtime re-quantization.
   - Dispatch fused multi-bank gather kernels (`copy_missing`) directly into GPU slot caches, preventing intermediate buffer repacking allocations.
</HETEROGENEOUS_MEMORY_TIERING_DOCTRINE>
