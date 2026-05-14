import os
import json
import logging
import numpy as np
from typing import List, Optional

logger = logging.getLogger("LaSERRetriever")

_LASER_PATH = "breeding_vat/data/model_zoo/LaSER-Qwen3-0.6B"
_CACHE_PATH = "breeding_vat/data/laser_kb_cache.json"


class LaSERRetriever:
    """
    Semantic KB retrieval using LaSER-Qwen3-4B as a dense retriever.

    LaSER is a Qwen3-4B fine-tuned for embedding/retrieval.  We use mean-pool
    of the last hidden states as the document/query embedding (standard for
    causal-LM-based dense retrievers).

    CPU-only: the UI container has no GPU, so inference is slow but single
    short queries are fine (~1-2 s per query after the model is loaded).
    Chunk embeddings are precomputed and cached to disk so startup cost is paid
    once.

    Usage:
        retriever = LaSERRetriever()
        retriever.index_documents(["docs/guides/ADVISOR_KNOWLEDGE_BASE.md", ...])
        chunks = retriever.retrieve("Which method works best for reasoning?", top_k=3)
    """

    def __init__(self, model_path: str = _LASER_PATH, cache_path: str = _CACHE_PATH):
        self.model_path = model_path
        self.cache_path = cache_path
        self.model = None
        self.tokenizer = None
        self.chunks: List[str] = []
        self.embeddings: Optional[np.ndarray] = None
        self._loaded = False

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _load_model(self):
        if self._loaded:
            return
        if not os.path.exists(self.model_path):
            raise FileNotFoundError(f"LaSER model not found at {self.model_path}")

        import torch
        from transformers import AutoModel, AutoTokenizer

        logger.info(f"Loading LaSER from {self.model_path} (CPU)")
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_path)
        self.model = AutoModel.from_pretrained(
            self.model_path,
            torch_dtype=torch.float16,
            device_map="cpu",
        )
        self.model.eval()
        self._loaded = True
        logger.info("LaSER ready")

    def _embed(self, texts: List[str]) -> np.ndarray:
        import torch

        self._load_model()
        vecs = []
        for text in texts:
            inputs = self.tokenizer(
                text, return_tensors="pt", truncation=True, max_length=512
            )
            with torch.no_grad():
                out = self.model(**inputs, output_hidden_states=True)
                # mean-pool last hidden state over sequence length
                vec = out.last_hidden_state.mean(dim=1).squeeze().float().numpy()
            vecs.append(vec)
        return np.array(vecs)

    def _cosine(self, q: np.ndarray, docs: np.ndarray) -> np.ndarray:
        q_n = q / (np.linalg.norm(q) + 1e-8)
        d_n = docs / (np.linalg.norm(docs, axis=1, keepdims=True) + 1e-8)
        return d_n @ q_n

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def index_documents(self, doc_paths: List[str], chunk_chars: int = 500):
        """
        Chunk and embed documents, then save to cache.

        Splits on double-newlines (paragraph boundaries) and packs paragraphs
        into chunks of ~chunk_chars characters.
        """
        self.chunks = []

        for path in doc_paths:
            if not os.path.exists(path):
                logger.warning(f"Skipping missing file: {path}")
                continue
            try:
                text = open(path, encoding="utf-8").read()
                paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
                current = ""
                for para in paragraphs:
                    if len(current) + len(para) < chunk_chars:
                        current = (current + "\n\n" + para).strip()
                    else:
                        if current:
                            self.chunks.append(current)
                        current = para
                if current:
                    self.chunks.append(current)
                logger.info(f"Indexed {path}: {len(paragraphs)} paragraphs")
            except Exception as e:
                logger.warning(f"Failed to read {path}: {e}")

        if not self.chunks:
            logger.warning("No chunks produced — nothing to embed")
            return

        logger.info(f"Embedding {len(self.chunks)} chunks with LaSER...")
        self.embeddings = self._embed(self.chunks)

        try:
            os.makedirs(os.path.dirname(self.cache_path) or ".", exist_ok=True)
            with open(self.cache_path, "w", encoding="utf-8") as f:
                json.dump(
                    {"chunks": self.chunks, "embeddings": self.embeddings.tolist()},
                    f,
                )
            logger.info(f"Embedding cache saved to {self.cache_path}")
        except Exception as e:
            logger.warning(f"Cache save failed: {e}")

    def load_cache(self) -> bool:
        """Load pre-computed embeddings from disk. Returns True on success."""
        if not os.path.exists(self.cache_path):
            return False
        try:
            data = json.load(open(self.cache_path, encoding="utf-8"))
            self.chunks = data["chunks"]
            self.embeddings = np.array(data["embeddings"])
            logger.info(f"Loaded {len(self.chunks)} cached chunks")
            return True
        except Exception as e:
            logger.warning(f"Cache load failed: {e}")
            return False

    def retrieve(self, query: str, top_k: int = 3) -> List[str]:
        """
        Return the top_k most semantically relevant KB chunks for query.
        Falls back to empty list if no index is available.
        """
        if self.embeddings is None:
            if not self.load_cache():
                logger.warning("No index available for retrieval")
                return []

        q_emb = self._embed([query])[0]
        sims = self._cosine(q_emb, self.embeddings)
        top_idx = np.argsort(sims)[-top_k:][::-1]
        return [self.chunks[i] for i in top_idx]
