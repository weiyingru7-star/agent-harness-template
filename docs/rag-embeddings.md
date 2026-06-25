# RAG Embeddings 嵌入层

V0.4.4 为 RAG Pipeline 增加 embedding provider 抽象层。当前只实现 `MockEmbeddingProvider`，不接真实 embedding API。

## 设计目标

- 定义 embedding request/result/provider contract。
- 实现确定性的 MockEmbeddingProvider，用于测试 provider contract。
- 提供 EmbeddingRegistry 供按名称获取 provider。
- 不集成到 ingest 或 retrieve 流程——V0.4.4 只定义接口。

## 核心模型

### EmbeddingRequest

```python
class EmbeddingRequest(BaseModel):
    input: str | list[str]         # 单个文本或批量文本
    model: str = "mock-embedding"  # provider 名称
    dimensions: int | None = None  # 可选维度覆盖
    metadata: dict = {}
```

### EmbeddingResult

```python
class EmbeddingResult(BaseModel):
    embeddings: list[list[float]]  # 向量列表
    model: str                     # 实际 model
    dimensions: int                # 向量维度
    usage: dict = {}               # token 计数等
    metadata: dict = {}
```

## EmbeddingProvider Interface

```python
class EmbeddingProvider(ABC):
    @property
    def provider_name(self) -> str: ...
    def embed(self, request: EmbeddingRequest) -> EmbeddingResult: ...
```

V0.4.4 只实现 `MockEmbeddingProvider`。

## MockEmbeddingProvider

确定性伪嵌入引擎：

1. 对文本取 `md5` 哈希生成种子
2. 用 LCG（线性同余生成器）生成 8 维向量
3. L2 归一化
4. 相同输入 → 相同 embedding；不同输入 → 不同 embedding
5. 默认维度 8，可通过 `dimensions` 覆盖

不调用外部 API，不追求语义质量。

## EmbeddingRegistry

```python
# 注册
EmbeddingRegistry.register(MockEmbeddingProvider())

# 获取
provider = EmbeddingRegistry.get("mock-embedding")

# 列表
providers = EmbeddingRegistry.list_providers()  # ["mock-embedding"]
```

MockEmbeddingProvider 在 `harness/rag/__init__.py` 导入时自动注册。

## Smoke API

`POST /api/knowledge/embeddings/smoke`

```json
{"input": "hello", "provider": "mock-embedding"}
→ {"dimensions": 8, "model": "mock-embedding", "count": 1, "usage": {}}
```

仅用于验证 provider 正常工作。

## 与现有 RAG Pipeline 的关系

- keyword retrieve / citation / RAG eval 完全不受影响。
- ingest 中未集成 embedding。后续 V0.4.x 可以在 chunking 后调用 embedding provider，将 embedding 存入向量结构或 metadata。
- MockEmbeddingProvider 可作为测试桩，后续替换为真实 provider。

## 验收

```bash
python3 scripts/check_business_terms.py
make test-api
python3 scripts/run_evals.py
python3 scripts/run_rag_evals.py
```
