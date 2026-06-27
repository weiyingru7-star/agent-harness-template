# Offline Document Ingestion Pipeline 离线文档清洗流水线

V1.5 离线文档清洗和入库流水线，用于把原始文档变成可检索的 RAG chunks。

## 支持的文件类型

- `.txt` — 纯文本
- `.md` — Markdown（保留标题）
- `.pdf` — 文字型 PDF（非 OCR）
- `.docx` — Word 文档（段落 + 表格）
- `.csv` — CSV 表格
- `.xlsx` — Excel 表格

## 流水线步骤

```
raw documents → clean_documents.py → cleaned/ → ingest_cleaned_docs.py → RAG store
```

### Step 1: clean_documents.py

读取 input-dir 中的原始文档，执行：
1. **Parse** — 根据文件扩展名选择合适的解析器，提取文本
2. **Clean** — 去除噪音（多余空行、页码、页眉页脚等）
3. **Preview chunk** — 生成预览 chunks 用于质量检查
4. **Output** — 写入 manifest.json、documents/、chunks/

### Step 2: ingest_cleaned_docs.py

读取 cleaned output，执行：
1. 读取 manifest.json
2. 对每个 document-level cleaned text 调用 KnowledgeStore.ingest_text()
3. **最终 chunking 由 RAG chunker 重新生成**
4. 传入 metadata：tenant_id / document_id / document_key / source_hash 等

## Preview chunks vs 最终入库 chunks

- `clean_documents.py` 生成 `chunks/` 预览 chunks 用于 QA
- `ingest_cleaned_docs.py` 按 document-level cleaned text 入库
- 最终 chunks 由 RAG chunker 重新生成，可能与预览不完全一致

## 命令

```bash
# 清洗文档（预览模式，不写文件）
python3 scripts/clean_documents.py \
  --tenant-id tenant_demo \
  --input-dir data/raw/tenant_demo \
  --output-dir data/cleaned/tenant_demo \
  --dry-run

# 清洗文档（实际写入）
python3 scripts/clean_documents.py \
  --tenant-id tenant_demo \
  --input-dir data/raw/tenant_demo \
  --output-dir data/cleaned/tenant_demo

# 入库清洗后的文档
python3 scripts/ingest_cleaned_docs.py \
  --tenant-id tenant_demo \
  --input-dir data/cleaned/tenant_demo
```

## 输出目录结构

```
data/cleaned/<tenant_id>/
├── manifest.json              # 文档和 chunks 元数据
├── documents/                 # 清洗后的文档文本（用于最终入库）
│   ├── readme.cleaned.md
│   └── ...
└── chunks/                    # 预览 chunks（用于 QA）
    ├── readme_000.json
    └── ...
```

## Metadata 字段

| 字段 | 说明 | V1.5 行为 |
|---|---|---|
| tenant_id | 租户标识 | 写入 document + chunk metadata |
| document_id | 文档 ID | 自动生成 |
| document_key | 文档 Key | 无扩展名的文件名 |
| document_version | 版本号 | 固定为 1（预留 V2.0） |
| source_hash | 来源 SHA256 | 记录，用于未来去重 |
| source_filename | 原始文件名 | 记录 |
| status | 状态 | 固定为 "active"（预留 V2.0） |

## 依赖安装

```bash
# 基础依赖（pip 安装时自动处理）
# PDF / DOCX / XLSX 解析需要可选依赖：
pip install pdfminer.six python-docx openpyxl

# 或通过项目 optional dependency group
pip install -e "apps/api[ingestion]"
```

## V1.5 范围

### 当前支持

- ✅ txt / md / pdf / docx / csv / xlsx 解析
- ✅ 基础文本清洗（去噪音、去页码、去空白）
- ✅ 类型感知的预览 chunking
- ✅ Manifest 输出（document + chunk metadata）
- ✅ 文档级入库（Plan A — RAG chunker 负责最终 chunking）
- ✅ tenant_id 贯穿流水线（V1.4 兼容）
- ✅ metadata 保留（document_key, source_hash, document_version, status）

### 当前不支持

- ❌ OCR（扫描件）
- ❌ PPT / 图片 / 网页 / 邮箱
- ❌ 异步队列 / Worker
- ❌ 文件上传 API / 商家自助页面
- ❌ 知识库版本迭代（新旧版切换）
- ❌ RBAC / 岗位权限
- ❌ Tool permission guard
