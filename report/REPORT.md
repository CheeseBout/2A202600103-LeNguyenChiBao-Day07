# Báo Cáo Lab 7: Embedding & Vector Store

**Họ tên:** Lê Nguyễn Chí Bảo
**Nhóm:** Z1
**Ngày:** 10/4/2026

---

## 1. Warm-up (5 điểm)

### Cosine Similarity (Ex 1.1)

**High cosine similarity nghĩa là gì?**
> *Viết 1-2 câu:*
Cosine similarity dùng để tính góc giữa 2 vector embedding. Công thức: tích vô hướng chia tích độ dài. Kết quả trong khoảng [-1; 1]. Nếu kết quả = -1, trái nghĩa/đối lập, kết quả = 1 thì giống nhau/tương đồng

**Ví dụ HIGH similarity:**
- Sentence A: Chiếc điện thoại mới của tôi có thời lượng pin ấn tượng
- Sentence B: Pin của thiết bị di động mà tôi vừa mua dùng được rất lâu
- Tại sao tương đồng: "Chiếc điện thoại" tương úng với "thiết bị di động", "mới" tương ứng với "vừa mua" và cách diễn đạt của 2 câu đều nói về thời lượng sử dụng của điện thoại mới mua.

**Ví dụ LOW similarity:**
- Sentence A: "Hôm nay thời tiết oi bức"
- Sentence B: "AI giúp ta tiết kiệm được rất nhiều thời gian làm những công việc lặp lại"
- Tại sao khác: Về ngữ nghĩa thì hai câu đang nói về 2 chủ đề khác nhau (thời tiết và AI), về mặt từ ngữ thì không có từ nào có ý nghĩa tương đồng nhau cả

**Tại sao cosine similarity được ưu tiên hơn Euclidean distance cho text embeddings?**
> *Viết 1-2 câu:*
Cosine similarity chỉ đo góc giữa hai vector, không phụ thuộc vào độ dài của vector như Euclidean (nếu vector A lặp từ "AI" 2 lần và vector B lặp 100 lần thì Euclidean sẽ lớn, dẫn đến kết luận không tương đồng)

### Chunking Math (Ex 1.2)

**Document 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
> *Trình bày phép tính:*
Chu đầu tiên luôn được trọn vẹn = chunk_size = 500
Từ chunk thứ 2 trở đi, chunk_size vẫn cố định là 500 nhưng sẽ trừ đi phần overlap = 50 => từ chunk thứ 2 trở đi, số token "mới" sẽ chỉ là 450
10000 - 500 = 9500 / 450 = xấp xỉ 21.11
Làm tròn lên 22 để tránh việc loại bỏ một số ký tự cuối cùng, sau đó cộng với chunk đầu tiên
> *Đáp án:* 23 chunks

**Nếu overlap tăng lên 100, chunk count thay đổi thế nào? Tại sao muốn overlap nhiều hơn?**
> *Viết 1-2 câu:*
Nếu overlap tăng lên 100,
(10000 - 500) / (500 - 100) = 23.75
Làm tròn lên 24 và cộng thêm chunk đầu tiên sẽ là tổng cộng 25 chunks
Overlap nhiều hơn giúp tránh trình trạng bị ngắt quãng thông tin quan trọng, giả sử chunk 1 chứa nửa đầu của một câu và chunk 2 chứa nửa sau của 1 câu thì cả hai chunk có thể gây khó hiểu cho AI nếu overlap thấp
---

## 2. Document Selection — Nhóm (10 điểm)

### Domain & Lý Do Chọn

**Domain:** [ví dụ: Customer support FAQ, Vietnamese law, cooking recipes, ...]
Luật

**Tại sao nhóm chọn domain này?**
> *Viết 2-3 câu:*
Nhóm chọn domain Luật vì đây là lĩnh vực về yêu cầu độ chính xác rất khắt khe khi trả lời và nhóm muốn được thử thách 


### Data Inventory

| # | Tên / Mô tả tài liệu | Nguồn | Số ký tự (ước tính) | Metadata đã gán |
|---|----------------------|-------|---------------------|-----------------|
| 1 | Xử phạt vượt đèn đỏ — xe ô tô, xe máy, xe đạp, người đi bộ (Nghị định 168/2024/NĐ-CP, Điều 6, 7, 9, 10) | legal_documents.md | ~900 | doc_id=1, category=giao_thông, law=NĐ168/2024 |
| 2 | Thu hồi đất do vi phạm pháp luật đất đai (Luật Đất đai 2024, Điều 81) | legal_documents.md | ~1200 | doc_id=2, category=đất_đai, law=LĐĐ2024 |
| 3 | Phạt không có giải pháp ngăn cháy khu vực sạc xe điện (Nghị định 106/2025/NĐ-CP, Điều 12) | legal_documents.md | ~700 | doc_id=3, category=phòng_cháy, law=NĐ106/2025 |
| 4 | Vi phạm Luật Bảo hiểm xã hội 2024 — xử phạt hành chính, kỷ luật, hình sự (Điều 132) | legal_documents.md | ~400 | doc_id=4, category=bảo_hiểm_xã_hội, law=LBHXH2024 |
| 5 | Nguyên tắc bảo vệ môi trường (Luật BVMT 2020, Điều 4) | legal_documents.md | ~1100 | doc_id=5, category=môi_trường, law=LBVMT2020 |
| 6 | Điều kiện chào bán trái phiếu ra công chúng (Luật Chứng khoán 2019, Điều 15) | legal_documents.md | ~900 | doc_id=6, category=chứng_khoán, law=LCK2019 |
| 7 | Chuyển người lao động làm công việc khác so với hợp đồng (BLLĐ 2019, Điều 29) | legal_documents.md | ~500 | doc_id=7, category=lao_động, law=BLLĐ2019 |
| 8 | Mức lương tối thiểu vùng 2024 theo Nghị định 74/2024/NĐ-CP | legal_documents.md | ~700 | doc_id=8, category=lao_động, law=NĐ74/2024 |

### Metadata Schema

| Trường metadata | Kiểu | Ví dụ giá trị | Tại sao hữu ích cho retrieval? |
|----------------|------|---------------|-------------------------------|
| doc_id | string | doc_2 | Dùng để truy vết chunk về đúng tài liệu gốc và hỗ trợ thao tác xóa/cập nhật theo tài liệu. |
| category | string | đất_đai | Cho phép pre-filter theo lĩnh vực pháp luật trước khi similarity search, giúp giảm nhiễu khi truy vấn. |
| law | string | LĐĐ2024 | Khoanh vùng đúng văn bản pháp luật cần tra cứu (theo luật/nghị định), tăng độ chính xác top-k. |

---

## 3. Chunking Strategy — Cá nhân chọn, nhóm so sánh (15 điểm)

### Baseline Analysis

Chạy `ChunkingStrategyComparator().compare()` trên 2-3 tài liệu:

| Tài liệu | Strategy | Chunk Count | Avg Length | Preserves Context? |
|-----------|----------|-------------|------------|-------------------|
| legal_documents.md | FixedSizeChunker (`fixed_size`) | 380 | 199.88 | Trung bình |
| legal_documents.md | SentenceChunker (`by_sentences`) | 69 | 824.04 | Tốt |
| legal_documents.md | RecursiveChunker (`recursive`) | 9376 | 5.04 | Kém |

### Strategy Của Tôi

**Loại:** [FixedSizeChunker / SentenceChunker / RecursiveChunker / custom strategy]
Sliding window + Overlap

**Mô tả cách hoạt động:**
> *Viết 3-4 câu: strategy chunk thế nào? Dựa trên dấu hiệu gì?*
Sliding window + Overlap chia văn bản thành các đoạn có độ dài cố định và cho phép các đoạn kế tiếp chồng lấn một phần nội dung. Phần overlap giúp giữ lại ngữ cảnh ở ranh giới giữa hai chunk, nên một câu hoặc một điều luật bị tách đôi vẫn còn xuất hiện ở chunk kế tiếp. Cách này đặc biệt phù hợp khi văn bản dài và nhiều ý quan trọng nằm sát nhau. Nó cũng giúp retrieval ổn định hơn vì truy vấn có thể khớp với nhiều đoạn liên tiếp chứa cùng căn cứ pháp lý.

**Tại sao tôi chọn strategy này cho domain nhóm?**
> *Viết 2-3 câu: domain có pattern gì mà strategy khai thác?*
Tài liệu pháp luật thường có cấu trúc dài, nhiều câu chứa điều khoản, khoản, điểm và phần điều kiện đi kèm nhau. Nếu chia quá cứng theo ranh giới cố định thì có thể làm mất ngữ cảnh pháp lý quan trọng ở cuối hoặc đầu đoạn. Sliding window + Overlap giữ được cả nội dung chính lẫn phần liên kết giữa các quy định, nên phù hợp cho retrieval trong domain luật. 

**Code snippet (nếu custom):**
```python
# Paste implementation here
```

### So Sánh: Strategy của tôi vs Baseline

| Tài liệu | Strategy | Chunk Count | Avg Length | Retrieval Quality? |
|-----------|----------|-------------|------------|--------------------|
| legal_documents.md | SentenceChunker (`by_sentences`) | 69 | 824.04 | Tốt |
| legal_documents.md | Sliding Window + Overlap (`custom`) | 138 | 546.04 | Tốt |

### So Sánh Với Thành Viên Khác

Bạn có thể điền nhanh như sau:

| Thành viên | Strategy | Retrieval Score (/10) | Điểm mạnh | Điểm yếu |
|-----------|----------|----------------------|-----------|----------|
| Tôi | Sliding Window | 0 | Dễ triển khai, tốc độ xử lý tốt, giữ được một phần ngữ cảnh nhờ overlap. | Cắt theo độ dài nên dễ làm vỡ ý pháp lý; phụ thuộc mạnh vào chất lượng embedding, kém với query khác diễn đạt. |
| Tuấn Anh | Recursive | 9 | Linh hoạt theo nhiều mức tách, xử lý được tài liệu dài và không đồng đều cấu trúc. | Nếu separator chưa tối ưu sẽ tạo nhiều chunk ngắn/nhiễu; khó kiểm soát độ ổn định giữa các loại văn bản. |
| Đức | Parent-Child | 2 | Giữ cân bằng giữa ngữ cảnh rộng (parent) và chi tiết (child), dễ truy vết nguồn. | Thiết kế phức tạp hơn, tốn tài nguyên lập chỉ mục; nếu map parent-child không tốt thì retrieval giảm rõ. |
| Nguyên | Document-structure | 3 | Khai thác tiêu đề/mục/điều khoản nên hợp tài liệu pháp lý, chunk có tính logic cao. | Phụ thuộc chất lượng cấu trúc tài liệu đầu vào; tài liệu không chuẩn định dạng thì hiệu quả giảm. |
| Huân | Semantic | 3 | Bám ý nghĩa tốt hơn keyword thuần, xử lý tốt paraphrase khi embedding đủ mạnh. | Nhạy với model embedding và ngôn ngữ; chi phí tính toán cao hơn, khó debug nguyên nhân sai lệch. |
| Thắng | Agentic | 2 | Có khả năng lập kế hoạch truy xuất nhiều bước, tổng hợp câu trả lời linh hoạt. | Dễ sinh nhiễu khi truy xuất nhiều bước; khó kiểm soát tính nhất quán và độ chính xác nếu retrieval nền chưa tốt. |

**Strategy nào tốt nhất cho domain này? Tại sao?**
Theo kết quả benchmark của nhóm, Recursive là strategy tốt nhất trong lần thử này vì đạt 9/10, cao hơn các phương pháp còn lại.
Recursive tách theo nhiều mức phân cách nên giữ được ngữ cảnh đủ dài, đồng thời vẫn linh hoạt xử lý các đoạn văn pháp lý có cấu trúc không đồng đều.
Tuy vậy, strategy này vẫn cần tinh chỉnh separator và ngưỡng chunk_size để tránh sinh nhiều chunk nhiễu ở một số tài liệu đặc thù.

---

## 4. My Approach — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi implement các phần chính trong package `src`.

### Chunking Functions

**`SentenceChunker.chunk`** — approach:
Sử dụng regex để tách văn bản thành list các câu dựa trên dấu câu như: ".", "?", "!" và khoảng trắng. Sau đó gom các câu lại thành chunk

**`RecursiveChunker.chunk` / `_split`** — approach:
Phân tách theo một thứ tự ưu tiên (\n\n, \n, dấu chấm câu, khoảng trắng). Nếu sau khi chia mà chunk đó vượt quá chunk_size thì tiếp tục chia nhỏ theo thứ tự đã nêu

### EmbeddingStore

**`add_documents` + `search`** — approach:
add_documents: Chuyển doc gốc thành record sau đó thêm vào ids, documents, embeddings, metadatas vào record
search: embedding câu query của người dùng, tìm đoạn văn bản có độ tương đồng cao nhất


**`search_with_filter` + `delete_document`** — approach:
search_with_filter: embedding query của người dùng, so sánh độ tương đồng với filter
delete_document: xóa bằng cách truy xuất và loại bỏ toàn bộ record chứa doc_id trong phần metadata của chúng

### KnowledgeBaseAgent

**`answer`** — approach:
Trích xuất thông tin từ store để làm ngữ cảnh. Cấu trúc prompt gồm có 2 phần Context và Question. Prompt sau khi đã bao gồm Context sẽ được đưa cho LLM 

### Test Results

```
# Paste output of: pytest tests/ -v
```

**Số tests pass:** 42 / 42

---

## 5. Similarity Predictions — Cá nhân (5 điểm)

| Pair | Sentence A | Sentence B | Dự đoán | Actual Score | Đúng? |
|------|-----------|-----------|---------|--------------|-------|
| 1 | Mức lương tối thiểu vùng 2025 tỉnh Bắc Giang được xác định theo vùng như trên. | Mức lương tối thiểu vùng 2025 tỉnh Bắc Giang được xác định theo vùng như trên. | high | 1.0000 | Đúng |
| 2 | Đất cho thuê không đúng thẩm quyền sẽ bị thu hồi do vi phạm pháp luật về đất đai. | Đất cho thuê không đúng thẩm quyền sẽ bị thu hồi do vi phạm pháp luật về đất đai. | high | 1.0000 | Đúng |
| 3 | Người điều khiển xe máy vượt đèn đỏ bị phạt từ 4 đến 6 triệu đồng. | Xe mô tô không chấp hành đèn tín hiệu giao thông bị xử phạt 4-6 triệu đồng. | high | -0.0266 | Sai |
| 4 | Luật Dược sửa đổi 2024 cho phép bán thuốc online từ 01/07/2025. | Kho bạc Nhà nước thực hiện chức năng tổng kế toán nhà nước. | low | -0.1462 | Đúng |
| 5 | Người lao động thử việc phải được trả ít nhất 85% lương công việc. | Biển số nền trắng chữ đỏ ký hiệu NG cấp cho cơ quan ngoại giao. | low | 0.1130 | Đúng |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn nghĩa?**
Cặp số 3 là kết quả bất ngờ nhất vì hai câu gần nghĩa về cùng một hành vi vi phạm giao thông nhưng điểm lại rất thấp. Điều này cho thấy embedding mock trong lab không học ngữ nghĩa sâu, mà thiên về biểu diễn dựa trên chuỗi ký tự đầu vào nên rất nhạy với cách diễn đạt khác nhau.
Vì vậy khi đánh giá semantic retrieval, cần dùng embedding model có hiểu ngữ nghĩa thực sự thay vì chỉ dựa vào backend mock.

---

## 6. Results — Cá nhân (10 điểm)

Chạy 5 benchmark queries của nhóm trên implementation cá nhân của bạn trong package `src`. **5 queries phải trùng với các thành viên cùng nhóm.**

### Benchmark Queries & Gold Answers (nhóm thống nhất)

| # | Query | Gold Answer |
|---|-------|-------------|
| 1 | Quy trình thủ tục đăng ký cấp giấy phép lái xe ô tô mới năm 2025 gồm những bước nào? | "Căn cứ điểm b khoản 9; điểm b khoản 10; điểm d khoản 16 Điều 6 Nghị định 168/2024/NĐ-CP quy định xử phạt người điều khiển xe ô tô vượt đèn đỏ: phạt tiền từ 18.000.000 đồng đến 20.000.000 đồng và bị trừ 04 điểm giấy phép lái xe. Nếu gây tai nạn giao thông, phạt tiền từ 20.000.000 đồng đến 22.000.000 đồng và bị trừ 10 điểm giấy phép lái xe. Tương tự, Điều 7 quy định xử phạt người điều khiển xe máy vượt đèn đỏ với mức phạt tiền từ 4.000.000 đồng đến 6.000.000 đồng, bị trừ 04 điểm; nếu gây tai nạn, phạt từ 10.000.000 đồng đến 14.000.000 đồng và trừ 10 điểm. Điều 9 quy định phạt tiền từ 150.000 đồng đến 250.000 đồng đối với người điều khiển xe đạp, xe đạp máy vượt đèn đỏ. Điều 10 quy định phạt tiền từ 150.000 đồng đến 250.000 đồng đối với người đi bộ vượt đèn đỏ." |
| 2 | Điều kiện để được cấp giấy chứng nhận quyền sử dụng đất lần đầu là gì? | "Căn cứ khoản 35 Điều 3 Luật Đất đai 2024 quy định thu hồi đất là việc cơ quan nhà nước có thẩm quyền ban hành quyết định thu lại quyền sử dụng đất của người sử dụng đất hoặc thu lại đất của người đang sử dụng đất hoặc thu lại đất đang được Nhà nước giao quản lý. Điều kiện thu hồi đất do vi phạm pháp luật đất đai quy định tại Điều 81 Luật Đất đai 2024 bao gồm các trường hợp như sử dụng đất không đúng mục đích đã được Nhà nước giao, cho thuê, công nhận quyền sử dụng đất và đã bị xử phạt vi phạm hành chính mà tiếp tục vi phạm; người sử dụng đất hủy hoại đất và đã bị xử phạt vi phạm hành chính mà tiếp tục vi phạm; đất được giao, cho thuê không đúng đối tượng hoặc không đúng thẩm quyền; đất do nhận chuyển nhượng, nhận tặng cho từ người được Nhà nước giao đất, cho thuê đất mà người được giao đất, cho thuê đất không được chuyển nhượng, tặng cho theo quy định; đất được Nhà nước giao quản lý mà để bị lấn đất, chiếm đất; người sử dụng đất không thực hiện nghĩa vụ tài chính với Nhà nước; đất trồng cây hằng năm, đất nuôi trồng thủy sản không được sử dụng trong thời gian liên tục và đã bị xử phạt vi phạm hành chính mà không đưa đất vào sử dụng theo thời hạn ghi trong quyết định xử phạt vi phạm hành chính; đất được Nhà nước giao, cho thuê, cho phép chuyển mục đích sử dụng, công nhận quyền sử dụng đất, nhận chuyển nhượng quyền sử dụng đất để thực hiện dự án đầu tư mà không được sử dụng trong thời hạn liên tục kể từ khi nhận bàn giao đất trên thực địa hoặc tiến độ sử dụng đất chậm so với tiến độ ghi trong dự án đầu tư." |
| 3 | Điều kiện để được cấp giấy phép xây dựng công trình phòng cháy chữa cháy là gì? | "Căn cứ tại điểm a khoản 4 Điều 12 Nghị định 106/2025/NĐ-CP quy định về phạt tiền đối với hành vi không có giải pháp ngăn cháy đối với khu vực sạc điện cho xe động cơ điện tập trung trong nhà: Phạt tiền từ 40.000.000 đồng đến 50.000.000 đồng đối với cá nhân và từ 80.000.000 đồng đến 100.000.000 đồng đối với tổ chức. Biện pháp khắc phục hậu quả là buộc thực hiện giải pháp ngăn cháy đối với hành vi vi phạm. Luật Phòng cháy, chữa cháy và cứu nạn, cứu hộ 2024 quy định về phòng cháy trong lắp đặt, sử dụng điện cho sinh hoạt, sản xuất, bao gồm các điều kiện an toàn về phòng cháy như chấp hành quy định về an toàn điện, tư vấn lắp đặt, sử dụng thiết bị điện đảm bảo an toàn phòng cháy, sử dụng thiết bị sạc điện cho xe động cơ điện đảm bảo quy chuẩn kỹ thuật quốc gia, có giải pháp bảo đảm an toàn phòng cháy và trang bị phương tiện chữa cháy phù hợp." |
| 4 | Khi nào thì Luật Lao động 2023 có hiệu lực thi hành? | "Căn cứ theo khoản 2 Điều 132 Luật Bảo hiểm xã hội 2024 quy định: Cá nhân có hành vi vi phạm quy định của Luật này, tùy theo tính chất, mức độ vi phạm mà bị xử phạt vi phạm hành chính, xử lý kỷ luật hoặc bị truy cứu trách nhiệm hình sự; nếu gây thiệt hại thì phải bồi thường theo quy định của pháp luật. Cơ quan bảo hiểm xã hội có thẩm quyền xử lý vi phạm pháp luật về bảo hiểm xã hội bắt buộc theo khoản 7 Điều 17 Luật Bảo hiểm xã hội 2024." |
| 5 | Quy định pháp luật về thủ tục cấp giấy phép xây dựng nhà ở là gì? | "Căn cứ tại Điều 4 Luật Bảo vệ môi trường 2020 quy định về nguyên tắc bảo vệ môi trường như sau: [1] Bảo vệ môi trường là quyền, nghĩa vụ và trách nhiệm của mọi cơ quan, tổ chức, cộng đồng dân cư, hộ gia đình và cá nhân. [2] Bảo vệ môi trường là điều kiện, nền tảng, yếu tố trung tâm, tiên quyết cho phát triển kinh tế - xã hội bền vững. Hoạt động bảo vệ môi trường phải gắn kết với phát triển kinh tế, quản lý tài nguyên và được xem xét, đánh giá trong quá trình thực hiện các hoạt động phát triển. [3] Bảo vệ môi trường gắn kết hài hòa với an sinh xã hội, quyền trẻ em, bình đẳng giới, bảo đảm quyền mọi người được sống trong môi trường trong lành. [4] Hoạt động bảo vệ môi trường phải được tiến hành thường xuyên, công khai, minh bạch; ưu tiên dự báo, phòng ngừa ô nhiễm, sự cố, suy thoái môi trường, quản lý rủi ro về môi trường, giảm thiểu phát sinh chất thải, tăng cường tái sử dụng, tái chế chất thải để khai thác giá trị tài nguyên của chất thải. [5] Bảo vệ môi trường phải phù hợp với quy luật, đặc điểm tự nhiên, văn hóa, lịch sử, cơ chế thị trường, trình độ phát triển kinh tế - xã hội; thúc đẩy phát triển vùng đồng bào dân tộc thiểu số và miền núi. [6] Cơ quan, tổ chức, cộng đồng dân cư, hộ gia đình và cá nhân được hưởng lợi từ môi trường có nghĩa vụ đóng góp tài chính cho hoạt động bảo vệ môi trường; gây ô nhiễm, sự cố và suy thoái môi trường phải chi trả, bồi thường thiệt hại, khắc phục, xử lý và chịu trách nhiệm khác theo quy định của pháp luật. [7] Hoạt động bảo vệ môi trường bảo đảm không gây phương hại chủ quyền, an ninh và lợi ích quốc gia, gắn liền với bảo vệ môi trường khu vực và toàn cầu." |

### Kết Quả Của Tôi

| # | Query | Top-1 Retrieved Chunk (tóm tắt) | Score | Relevant? | Agent Answer (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 | Quy trình thủ tục đăng ký cấp giấy phép lái xe ô tô mới năm 2025 gồm những bước nào? | Nghị quyết 27-NQ/TW 2018 về cải cách tiền lương cán bộ, công chức, viên chức và lực lượng vũ trang. | 0.2498 | Không | Trả về context về cải cách tiền lương, không nêu quy trình cấp giấy phép lái xe. |
| 2 | Điều kiện để được cấp giấy chứng nhận quyền sử dụng đất lần đầu là gì? | Hướng dẫn 3789/HDLN-BHXH-LĐTBXH về báo cáo tình hình sử dụng lao động qua cổng dịch vụ công. | 0.2718 | Không | Trả về context về thủ tục báo cáo lao động, không phải điều kiện cấp giấy chứng nhận quyền sử dụng đất. |
| 3 | Điều kiện để được cấp giấy phép xây dựng công trình phòng cháy chữa cháy là gì? | Nghị định 156/2020/NĐ-CP về hành vi thao túng thị trường chứng khoán. | 0.3072 | Không | Trả về context về thao túng chứng khoán, không liên quan điều kiện cấp phép PCCC. |
| 4 | Khi nào thì Luật Lao động 2023 có hiệu lực thi hành? | Quyết định 391/QĐ-BTC 2025 về nhiệm vụ, quyền hạn của Bảo hiểm xã hội Việt Nam. | 0.2559 | Không | Trả về context về cơ quan BHXH, không chứa thông tin hiệu lực Luật Lao động 2023. |
| 5 | Quy định pháp luật về thủ tục cấp giấy phép xây dựng nhà ở là gì? | Điều 101 Luật Thi hành án dân sự 2008 về bán tài sản đã kê biên. | 0.3759 | Không | Trả về context về bán đấu giá tài sản kê biên, không phải thủ tục cấp phép xây dựng nhà ở. |

**Bao nhiêu queries trả về chunk relevant trong top-3?** 0 / 5
retrieval (mockup) hiện tại đang lệch miền dữ liệu khá nặng (trả về văn bản không liên quan cho toàn bộ bộ benchmark).
---

## 7. What I Learned (5 điểm — Demo)

**Điều hay nhất tôi học được từ thành viên khác trong nhóm:**
> *Viết 2-3 câu:*
Điều tôi học được rõ nhất từ các bạn là cách chọn strategy phải đi cùng cách đo kiểm cụ thể, không nên chỉ chọn theo cảm giác. Ví dụ, Recursive của bạn Tuấn Anh cho điểm cao vì separator và ngưỡng chunk được tinh chỉnh theo cấu trúc văn bản pháp lý. Nhờ đó tôi hiểu rằng cùng một domain nhưng chất lượng retrieval phụ thuộc rất nhiều vào cách triển khai chi tiết.

**Điều hay nhất tôi học được từ nhóm khác (qua demo):**
> *Viết 2-3 câu:*
Qua phần demo của nhóm khác, em học được cách ưu tiên metadata filtering trước khi similarity search để thu hẹp không gian tìm kiếm để giảm nhiễu khi truy vấn

**Nếu làm lại, tôi sẽ thay đổi gì trong data strategy?**
> *Viết 2-3 câu:*
Nếu có thể làm lại, em sẽ thu gọn corpus theo đúng phạm vi luật mà nhóm benchmark, thay vì trộn quá nhiều nguồn khác miền gây lệch retrieval, chuẩn hóa metadata bắt buộc như lĩnh vực, loại văn bản, năm ban hành và điều/khoản để lọc trước khi tìm kiếm vector

---

## Tự Đánh Giá

| Tiêu chí | Loại | Điểm tự đánh giá |
|----------|------|-------------------|
| Warm-up | Cá nhân | / 5 |
| Document selection | Nhóm | / 10 |
| Chunking strategy | Nhóm | / 15 |
| My approach | Cá nhân | / 10 |
| Similarity predictions | Cá nhân | / 5 |
| Results | Cá nhân | / 10 |
| Core implementation (tests) | Cá nhân | / 30 |
| Demo | Nhóm | / 5 |
| **Tổng** | | **/ 100** |
