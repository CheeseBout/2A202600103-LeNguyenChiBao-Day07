from __future__ import annotations

import argparse
import re
from pathlib import Path

try:
	from .chunking import ChunkingStrategyComparator
	from .embeddings import LocalEmbedder, OpenAIEmbedder, _mock_embed
	from .models import Document
	from .store import EmbeddingStore
except ImportError:
	import sys

	sys.path.append(str(Path(__file__).resolve().parent.parent))
	from src.chunking import ChunkingStrategyComparator
	from src.embeddings import LocalEmbedder, OpenAIEmbedder, _mock_embed
	from src.models import Document
	from src.store import EmbeddingStore


class CustomChunker:
	"""Sliding window chunker over words with overlap.

	This strategy keeps neighboring chunks semantically connected by
	reusing a tail of the previous chunk at the start of the next one.
	"""

	def __init__(self, chunk_size: int = 120, overlap: int = 30) -> None:
		self.chunk_size = max(1, chunk_size)
		self.overlap = max(0, min(overlap, self.chunk_size - 1))

	def chunk(self, text: str) -> list[str]:
		if not text or not text.strip():
			return []

		words = text.split()
		if len(words) <= self.chunk_size:
			return [" ".join(words)]

		step = self.chunk_size - self.overlap
		chunks: list[str] = []
		for start in range(0, len(words), step):
			end = min(start + self.chunk_size, len(words))
			chunk = " ".join(words[start:end]).strip()
			if chunk:
				chunks.append(chunk)
			if end >= len(words):
				break

		return chunks


def _load_legal_documents(path: Path) -> list[tuple[str, str]]:
	text = path.read_text(encoding="utf-8")
	pattern = r"# Document\s+(\d+)\n\n([\s\S]*?)(?=\n---\n\n# Document\s+|\Z)"
	matches = re.findall(pattern, text)
	return [(f"doc{doc_num}", content.strip()) for doc_num, content in matches]


def _get_embedding_fn(embedding_backend: str):
	if embedding_backend == "local":
		try:
			return LocalEmbedder()
		except Exception as exc:
			print(f"[WARN] Khong khoi tao duoc local embedding ({exc}), fallback sang mock.")
			return _mock_embed
	if embedding_backend == "openai":
		try:
			return OpenAIEmbedder()
		except Exception as exc:
			print(f"[WARN] Khong khoi tao duoc OpenAI embedding ({exc}), fallback sang mock.")
			return _mock_embed
	return _mock_embed


def run_retrieval_benchmark(embedding_backend: str = "mock") -> tuple[int, list[tuple[str, str, bool, float]]]:
	base_dir = Path(__file__).resolve().parent.parent
	data_path = base_dir / "data" / "legal_documents.md"

	chunker = CustomChunker(chunk_size=120, overlap=30)
	all_docs: list[Document] = []
	for doc_id, content in _load_legal_documents(data_path):
		chunks = chunker.chunk(content)
		for idx, chunk in enumerate(chunks):
			all_docs.append(
				Document(
					id=f"{doc_id}-chunk-{idx}",
					content=chunk,
					metadata={"doc_id": doc_id, "chunk_index": idx},
				)
			)

	embedding_fn = _get_embedding_fn(embedding_backend)
	store = EmbeddingStore(collection_name="sliding_chunker_benchmark", embedding_fn=embedding_fn)
	store.add_documents(all_docs)

	benchmarks: list[tuple[str, str]] = [
		("Phạt tiền xe ô tô vượt đèn đỏ theo Nghị định 168/2024/NĐ-CP là bao nhiêu?", "doc1"),
		("Các trường hợp thu hồi đất do vi phạm pháp luật đất đai theo Luật Đất đai 2024 là gì?", "doc2"),
		("Không có giải pháp ngăn cháy tại khu vực sạc xe điện bị xử phạt như thế nào?", "doc3"),
		("Vi phạm Luật Bảo hiểm xã hội 2024 có thể bị xử lý ra sao?", "doc4"),
		("Nguyên tắc bảo vệ môi trường theo Điều 4 Luật Bảo vệ môi trường 2020 là gì?", "doc5"),
		("Điều kiện chào bán trái phiếu ra công chúng theo Luật Chứng khoán 2019 gồm những gì?", "doc6"),
		("Người sử dụng lao động chuyển người lao động làm công việc khác phải tuân theo quy định nào?", "doc7"),
		("Mức lương tối thiểu vùng tại Bắc Giang theo Nghị định 74/2024/NĐ-CP là bao nhiêu?", "doc8"),
		("Luật Dược sửa đổi 2024 cho phép bán thuốc online từ khi nào?", "doc9"),
		("Đỗ xe ô tô ngược chiều lưu thông bị phạt tiền bao nhiêu?", "doc10"),
	]

	score = 0
	details: list[tuple[str, str, bool, float]] = []
	for query, expected_doc_id in benchmarks:
		results = store.search(query, top_k=3)
		top3_doc_ids = [r.get("metadata", {}).get("doc_id", "") for r in results]
		top1_score = float(results[0].get("score", 0.0)) if results else 0.0
		is_relevant = expected_doc_id in top3_doc_ids
		if is_relevant:
			score += 1
		details.append((query, expected_doc_id, is_relevant, top1_score))

	return score, details


def _parse_args() -> argparse.Namespace:
	parser = argparse.ArgumentParser(description="Sliding chunker benchmark")
	parser.add_argument(
		"--embedding",
		choices=["mock", "local", "openai"],
		default="mock",
		help="Chon backend embedding de benchmark retrieval",
	)
	return parser.parse_args()


if __name__ == "__main__":
	args = _parse_args()
	comparator = ChunkingStrategyComparator()
	compare_result = comparator.compare(text="Quy trình thủ tục đăng ký cấp giấy phép lái xe ô tô mới năm 2025 gồm những bước nào?")
	print(compare_result)
	print(f"Embedding backend: {args.embedding}")

	total_score, detail_rows = run_retrieval_benchmark(embedding_backend=args.embedding)
	for idx, (query, expected_doc_id, is_relevant, top1_score) in enumerate(detail_rows, 1):
		status = "+1" if is_relevant else "+0"
		print(f"Q{idx}: {status} | expected={expected_doc_id} | top1_score={top1_score:.4f} | query={query}")
	print(f"Retrieval score: {total_score}/10")
