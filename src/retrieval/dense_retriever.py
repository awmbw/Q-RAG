"""
Dense Retriever Module

Converts text into vector embeddings using a pre-trained model,
then finds the most relevant documents via cosine similarity.

This is the "candidate generation" step of our pipeline:
    Query → Embedding → Similarity Search → Top-n Candidates
"""

import numpy as np
from sentence_transformers import SentenceTransformer


class DenseRetriever:
    """
    Retrieves documents using dense (embedding-based) similarity.
    
    Why a class and not just functions?
    Because the embedding model needs to be loaded ONCE (takes ~2 seconds)
    and then reused for thousands of queries. A class holds the loaded model
    in self.model so we don't reload it every time.
    """
    
    def __init__(self, model_name="all-MiniLM-L6-v2"):
        """
        Initialize the retriever with a specific embedding model.
        
        Args:
            model_name: Name of the sentence-transformers model to use.
                "all-MiniLM-L6-v2" is:
                - Small (80MB) → fast to load
                - 384-dimensional embeddings → manageable vectors
                - Good quality for English text similarity
                - The most popular model for this task in industry
        """
        self.model_name = model_name
        self.model = None            # will be loaded lazily
        self.embedding_dim = None    # set after model loads
    
    def load_model(self):
        """
        Load the embedding model into memory (and GPU if available).
        
        We separate this from __init__ so you can create the object
        without immediately loading a large model into memory.
        This pattern is called "lazy loading."
        """
        print(f"Loading embedding model: {self.model_name}...")
        self.model = SentenceTransformer(self.model_name)
        self.embedding_dim = self.model.get_embedding_dimension()
        print(f"  ✅ Loaded. Embedding dimension: {self.embedding_dim}")
    
    def encode_texts(self, texts, batch_size=32, show_progress=True):
        """
        Convert a list of text strings into embedding vectors.
        
        Args:
            texts: List of strings to embed.
                   e.g., ["Arthur's Magazine was...", "First for Women is..."]
            batch_size: How many texts to process at once.
                        Larger = faster but uses more GPU memory.
            show_progress: Whether to show a progress bar.
        
        Returns:
            numpy array of shape (len(texts), embedding_dim)
            e.g., for 10 texts with MiniLM: shape (10, 384)
        """
        if self.model is None:
            self.load_model()
        
        embeddings = self.model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=show_progress,
            convert_to_numpy=True,      # return numpy array, not torch tensor
            normalize_embeddings=True    # L2 normalize so cosine similarity = dot product
        )
        return embeddings
    
    def compute_relevance_scores(self, query_embedding, doc_embeddings):
        """
        Compute cosine similarity between one query and multiple documents.
        
        Because we normalized the embeddings in encode_texts(),
        cosine similarity simplifies to a dot product:
            cos(a, b) = (a · b) / (||a|| * ||b||)
        When ||a|| = ||b|| = 1 (normalized), this becomes just a · b.
        
        Args:
            query_embedding: numpy array of shape (384,)
            doc_embeddings: numpy array of shape (n_docs, 384)
        
        Returns:
            numpy array of shape (n_docs,) with similarity scores
        """
        # Matrix-vector dot product: (n_docs, 384) @ (384,) → (n_docs,)
        scores = doc_embeddings @ query_embedding
        return scores
    
    def compute_pairwise_similarity(self, doc_embeddings):
        """
        Compute similarity between ALL pairs of documents.
        This gives us the REDUNDANCY MATRIX for the QUBO formulation.
        
        If doc i and doc j are very similar (high score), selecting
        both is wasteful — they contain the same information.
        
        Args:
            doc_embeddings: numpy array of shape (n_docs, 384)
        
        Returns:
            numpy array of shape (n_docs, n_docs)
            Entry [i][j] = cosine similarity between doc i and doc j
        """
        # Matrix multiplication: (n, 384) @ (384, n) → (n, n)
        # .T means "transpose" — flips rows and columns
        similarity_matrix = doc_embeddings @ doc_embeddings.T
        return similarity_matrix
    
    def retrieve(self, query, documents, top_n=None):
        """
        Full retrieval pipeline for a single query.
        
        Args:
            query: The question string.
            documents: List of document dicts (from our processed data),
                       each having at least a "text" field.
            top_n: How many top documents to return. 
                   None means return all, ranked by relevance.
        
        Returns:
            dict containing:
                - query_embedding: the query vector
                - doc_embeddings: matrix of document vectors
                - relevance_scores: similarity of each doc to query
                - pairwise_similarity: doc-to-doc similarity matrix
                - ranked_indices: document indices sorted by relevance
        """
        if self.model is None:
            self.load_model()
        
        # Step 1: Embed the query
        query_embedding = self.model.encode(
            query,
            normalize_embeddings=True,
            convert_to_numpy=True
        )
        
        # Step 2: Embed all candidate documents
        doc_texts = [doc["text"] for doc in documents]
        doc_embeddings = self.encode_texts(doc_texts, show_progress=False)
        
        # Step 3: Compute relevance scores (query ↔ each doc)
        relevance_scores = self.compute_relevance_scores(
            query_embedding, doc_embeddings
        )
        
        # Step 4: Compute pairwise similarity (doc ↔ doc) for redundancy
        pairwise_sim = self.compute_pairwise_similarity(doc_embeddings)
        
        # Step 5: Rank documents by relevance (highest first)
        # argsort returns indices that would sort the array (ascending)
        # [::-1] reverses it to get descending order
        ranked_indices = np.argsort(relevance_scores)[::-1]
        
        if top_n is not None:
            ranked_indices = ranked_indices[:top_n]
        
        return {
            "query_embedding": query_embedding,
            "doc_embeddings": doc_embeddings,
            "relevance_scores": relevance_scores,
            "pairwise_similarity": pairwise_sim,
            "ranked_indices": ranked_indices
        }
