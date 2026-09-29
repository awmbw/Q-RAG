# Quantum-Enhanced Retrieval-Augmented Generation (Q-RAG)

## Overview
This project bridges the gap between **Quantum Computing** and **Generative AI**. It implements a Quantum-Enhanced Retrieval-Augmented Generation (Q-RAG) pipeline that maps the problem of "Document Selection" into a Quantum Physics problem (Ising Hamiltonian) to dynamically optimize Large Language Model (LLM) context windows.

## The Problem: Greedy RAG
Standard RAG systems use a greedy "Top-K" selection method based purely on the cosine similarity between a query and a document. 
This leads to two critical flaws:
1. **Redundancy & Token Waste**: The top 5 documents might all contain the exact same information, wasting precious LLM token budget.
2. **Static Context**: Top-K forces the LLM to read exactly $K$ documents every time, whether the question requires 1 document or 10.

## The Quantum Solution: QUBO Formulation
We reformulate document selection as a **Quadratic Unconstrained Binary Optimization (QUBO)** problem. We ask a quantum optimizer to find the perfect subset of documents that maximizes relevance to the query, while simultaneously penalizing documents that are redundant to each other.

### The Mathematics
Let $N$ be the number of candidate documents. We define a binary variable $x_i \in \{0, 1\}$ for each document, where $x_i = 1$ means the document is selected.

The objective function to **minimize** is:

$$ \min_{x} \left( -\alpha \sum_{i=1}^{N} r_i x_i + \beta \sum_{i=1}^{N} \sum_{j=i+1}^{N} S_{ij} x_i x_j \right) $$

Where:
- $r_i$: Relevance score (Dot product between Query embedding and Document $i$ embedding).
- $S_{ij}$: Redundancy score (Dot product between Document $i$ embedding and Document $j$ embedding).
- $\alpha$: Hyperparameter controlling the weight of Relevance.
- $\beta$: Hyperparameter controlling the penalty for Redundancy.

---

## Architecture & Execution Flow

### 1. Data Pipeline (`notebooks/01`, `02`)
- **Dataset**: `HotpotQA` (a multi-hop reasoning dataset requiring synthesis across multiple documents).
- **Process**: Extracted a subset (1000 dev, 500 eval). Each question was paired with its 2 Ground Truth documents and 8 highly-ranked "Distractor" documents.

### 2. Dense Retrieval (`src/retrieval/dense_retriever.py`)
- **Model**: `all-MiniLM-L6-v2` (SentenceTransformers).
- **Process**: Embeds the query and the 10 candidate documents. It computes the relevance vector ($r_i$) and the crucial pairwise similarity matrix ($S_{ij}$) which maps the redundancy graph.

### 3. QUBO Formulation (`src/optimization/qubo_builder.py`)
- **Process**: Translates the matrices into a Qiskit `QuadraticProgram`. 
- **Graph Sparsification**: The script dynamically drops quadratic terms where $S_{ij} \le 0$, removing graph edges and making the problem significantly easier to map onto quantum hardware.

### 4. Quantum Optimization (`src/optimization/qaoa_solver.py` & `exact_solver.py`)
- **QAOA Solver**: Implements the Quantum Approximate Optimization Algorithm (QAOA) using Qiskit's `StatevectorSampler` and a classical `COBYLA` optimizer to find the minimum energy state.
- **Exact Solver**: Implements `NumPyMinimumEigensolver` to rapidly compute the true ground state for hyperparameter tuning.

### 5. LLM Generation (`src/generation/llm_generator.py`)
- **Model**: `Qwen/Qwen2.5-1.5B-Instruct`
- **Process**: The optimal subset of documents chosen by the Quantum Optimizer is concatenated into a context prompt. The SLM performs inference on the local GPU (RTX 5060) to synthesize the final answer.

---

## 📊 Evaluation & Results

To prove the efficacy of the QUBO formulation, we run a Hyperparameter Grid Search (tuning $\beta$) and evaluate the pipeline on a 500-question subset of HotpotQA.

### The "Goldilocks" Tune ($\alpha=1.0, \beta=0.2$)
By tuning $\beta$ to 0.2, the quantum optimizer was allowed to dynamically size the context window. 

| Metric | Standard RAG (Top-5) | Q-RAG ($\beta=0.2$) |
|--------|----------------------|----------------------|
| **Average Docs Selected** | 5.00 | **6.27** (Dynamic) |
| **Recall** | 83.4% | **87.3%** |

### Conclusion
1. **Dynamic Sizing**: Q-RAG proved it can dynamically adapt the number of selected documents based on the complexity of the redundancy matrix.
2. **Rescuing Relevant Documents**: By penalizing redundancy, Q-RAG successfully avoided grabbing 5 redundant distractor documents, opting instead for a diverse set that increased total Recall by nearly 4%.
3. **End-to-End Speed**: The complete pipeline (Embedding $\rightarrow$ Quantum Optimization $\rightarrow$ LLM Inference) executes in ~3.4 seconds locally.

---
*Built with Qiskit, HuggingFace Transformers, and PyTorch.*
