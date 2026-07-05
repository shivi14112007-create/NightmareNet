Hi @Adit-Jain-srm,

I've completed the implementation of Distributed multi-GPU cycle execution with fault-tolerant checkpointing for Issue #30. 

**Analysis of work completed:**
This PR introduces the entire native multi-GPU architecture. This required creating a completely new `distributed` package to handle low-level PyTorch DDP context initialization, memory-aware device pooling, phase-specific fallback strategies (e.g., using DDP for massive data throughput in Wake phase, but falling back for Compress phase), and atomic checkpoint/resume logic using configuration hashes and `.complete` sentinels to guarantee fault tolerance. Because this directly refactors the core execution strategy and pipeline of NightmareNet and addresses the most complex core abstraction for distributed training, it firmly fits under the **Core/Arch** category.

According to the official ECSoC26 Points System, core architectural implementations that significantly scale or refactor backend systems fall under Level 3 tasks.

Could you please review the PR, and if everything looks good, apply the `ECSoC26` label as well as the `Level 3` and `good-backend` labels?

Thank you!
