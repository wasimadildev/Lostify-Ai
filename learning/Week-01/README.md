# Lostify AI — Week 01
## AI Fundamentals & Image Similarity

### Week Objective

The objective of Week 01 was to understand the basic concepts required for the Lostify AI matching system and implement the first image-similarity prototype using a pretrained CLIP model.

The main pipeline implemented during this week was:

```text
Image
  ↓
Pretrained CLIP
  ↓
Image Embedding
  ↓
512-Dimensional Vector
  ↓
Normalization
  ↓
Cosine Similarity
  ↓
Similarity Score
```

The complete Lostify AI architecture will be developed gradually in the following weeks.

---

# 1. What I Learned

## 1.1 Artificial Intelligence

AI enables computer systems to perform tasks that normally require human intelligence.

For Lostify AI, AI is used to analyze images and find potentially similar existing lost/found cases.

## 1.2 Computer Vision

Computer vision allows computers to understand and process visual information such as images.

Lostify AI will use computer vision for:

- Image analysis
- Object detection
- Image similarity
- Face analysis
- Pet/item recognition
- OCR

## 1.3 Machine Learning Model

A machine learning model learns patterns from data and uses those learned patterns to perform a task.

For the first Lostify AI prototype, instead of training a model from scratch, a pretrained model is used.

---

# 2. Transfer Learning

Transfer learning means using knowledge learned by an existing pretrained model for a new application.

Instead of:

```text
Train model from scratch
        ↓
Large dataset
        ↓
Large computational resources
        ↓
Long training time
```

Lostify AI uses:

```text
Pretrained Model
       ↓
Reuse learned representation
       ↓
Lostify AI
```

This approach is more practical for the FYP because of the limited development time and dataset.

---

# 3. Pretrained CLIP Model

The first image-similarity experiment used:

```text
openai/clip-vit-base-patch32
```

CLIP provides an image encoder that converts an image into a numerical representation.

The basic process is:

```text
Image
  ↓
CLIP Image Encoder
  ↓
Image Features
  ↓
CLIP Projection
  ↓
512-dimensional embedding
```

---

# 4. Image Embedding

An embedding is a numerical representation of an image.

For example:

```text
cat.jpg
   ↓
CLIP
   ↓
[0.0064, 0.0017, 0.0218, ...]
```

The experiment produced:

```text
Embedding shape: torch.Size([1, 512])
```

Therefore, each image was represented by a 512-dimensional vector.

---

# 5. Vector

A vector is a list of numerical values.

Example:

```text
[0.0064, 0.0017, 0.0218, -0.0813, ...]
```

In the current Lostify AI experiment:

```text
1 image
   ↓
512 numerical values
```

These values represent learned visual information from the image.

---

# 6. Feature

A feature represents useful information extracted from data.

For an image, useful visual information may include:

- Shape
- Texture
- Appearance
- Visual structure
- Objects

Instead of manually defining these features, the pretrained model learns a numerical representation.

```text
Image
 ↓
CLIP
 ↓
Visual Features
 ↓
Embedding
```

---

# 7. Vector Normalization

The generated embedding was normalized before similarity calculation.

The implementation used:

```python
image_features = image_features / image_features.norm(
    dim=-1,
    keepdim=True
)
```

Normalization makes the vector length approximately equal to 1.

The purpose is to make similarity comparisons more consistent when using cosine similarity.

---

# 8. Cosine Similarity

Cosine similarity measures the similarity between two vectors based on the angle/direction between them.

Conceptually:

```text
Vector A
   ↘
    ↘
     ↘ Vector B
```

If two vectors point in similar directions, their cosine similarity is higher.

The formula is:

```text
cosine_similarity =
(A · B) / (||A|| × ||B||)
```

For Lostify AI:

```text
Image 1
   ↓
Embedding 1

Image 2
   ↓
Embedding 2

Embedding 1
     ↕
Cosine Similarity
     ↕
Embedding 2
```

---

# 9. Similarity Score

The similarity experiment produced:

```text
Cat 1 ↔ Cat 2: 0.7412
Cat 1 ↔ Dog:   0.6956
```

Therefore:

```text
0.7412 > 0.6956
```

The model considered Cat 2 more visually similar to Cat 1 than the tested Dog image.

### Important

The value `0.7412` should **not** automatically be interpreted as `74.12% probability`.

It is a similarity score.

---

# 10. Query Image

The new image that we want to search with is called the **query**.

For Lostify:

```text
New Lost Report Image
        ↓
      Query
```

Example:

```text
query.jpg
```

The query is converted into an embedding and compared with existing case embeddings.

---

# 11. Candidate Cases

Existing Lostify cases become candidates for matching.

For example:

```text
Query
  ↓
CASE-001
CASE-002
CASE-003
CASE-004
...
CASE-010
```

The system calculates similarity between the query and each candidate.

---

# 12. Similarity Search

Similarity search means finding the existing records whose embeddings are most similar to a query embedding.

The planned Lostify workflow is:

```text
Query Image
     ↓
Embedding
     ↓
Compare with existing case embeddings
     ↓
Similarity scores
     ↓
Ranking
     ↓
Top-5 Cases
```

---

# 13. Ranking

After calculating similarity scores, the cases are ordered from highest similarity to lowest similarity.

Example:

```text
CASE-003 → 0.91
CASE-005 → 0.87
CASE-008 → 0.84
CASE-001 → 0.81
CASE-009 → 0.76
```

This produces the ranked results.

---

# 14. Top-K

Top-K means returning the best K results.

For Lostify:

```text
K = 5
```

Therefore:

```text
Top-K = Top-5
```

The planned output is:

```text
1. CASE-003
2. CASE-005
3. CASE-008
4. CASE-001
5. CASE-009
```

---

# 15. FAISS — Concept Learned

FAISS was identified as the vector-search component for the later implementation.

Its planned role is:

```text
Existing Case Embeddings
        ↓
      FAISS
        ↑
        │
 Query Embedding
        ↓
 Top-K Similar Cases
```

### Week 01 status

```text
Understanding: ✅
Implementation: ⏳ Next stage
```

FAISS is not part of the completed Week 01 implementation yet.

---

# 16. Text Embeddings — Future Work

Lostify AI will eventually use more than images.

A report contains:

```text
Title
Description
Image
Location
```

CLIP can also generate text embeddings.

Planned future pipeline:

```text
Title
  ↓
CLIP Text Encoder
  ↓
Text Embedding
```

and:

```text
Description
  ↓
CLIP Text Encoder
  ↓
Text Embedding
```

This will later be combined with image similarity.

### Week 01 status

```text
Concept: ✅
Implementation: ⏳ Future week
```

---

# 17. Week 01 Implementation

## Implemented

### 1. Pretrained CLIP loading

```text
openai/clip-vit-base-patch32
```

### 2. Image loading

Images were loaded using PIL.

### 3. Image preprocessing

CLIP's processor was used to prepare images for the model.

### 4. Image feature extraction

The CLIP vision model was used to obtain visual features.

### 5. CLIP projection

The visual representation was projected into CLIP's embedding space.

### 6. Embedding normalization

The resulting vector was normalized.

### 7. 512-dimensional embedding

The experiment successfully generated:

```text
torch.Size([1, 512])
```

### 8. Cosine similarity experiment

Two image comparisons were performed:

```text
Cat 1 ↔ Cat 2: 0.7412
Cat 1 ↔ Dog:   0.6956
```

---

# 18. Week 01 Checklist

## AI Concepts

- [x] Understand Artificial Intelligence
- [x] Understand Computer Vision
- [x] Understand Machine Learning models
- [x] Understand pretrained models
- [x] Understand transfer learning
- [x] Understand embeddings
- [x] Understand vectors
- [x] Understand features
- [x] Understand vector normalization
- [x] Understand cosine similarity
- [x] Understand similarity scores
- [x] Understand query images
- [x] Understand candidate cases
- [x] Understand ranking
- [x] Understand Top-K
- [x] Understand similarity search concept
- [x] Understand the role of FAISS
- [ ] Implement FAISS
- [ ] Implement text embeddings
- [ ] Implement multimodal matching
- [ ] Implement YOLO

---

# 19. Practical Implementation Checklist

## Environment

- [x] Python environment configured
- [x] PyTorch installed
- [x] Transformers installed
- [x] PIL/Pillow installed

## CLIP

- [x] Download pretrained CLIP
- [x] Load CLIP model
- [x] Load CLIP processor
- [x] Load image
- [x] Preprocess image
- [x] Generate visual features
- [x] Project visual features
- [x] Generate 512-dimensional embedding
- [x] Normalize embedding

## Similarity

- [x] Generate embedding for Image 1
- [x] Generate embedding for Image 2
- [x] Calculate cosine similarity
- [x] Compare similarity scores
- [x] Understand which image is more similar

## Retrieval

- [x] Create 5–10 Lostify case images
- [x] Create one query image
- [x] Compare query with all cases
- [x] Sort similarity scores
- [x] Return Top-5 cases

The last five tasks are the immediate practical task that carries into the beginning of Week 02.

---

# 20. Week 01 Project Deliverable

At the end of Week 01, the AI component has a working **image embedding and similarity proof of concept**:

```text
                 IMAGE
                   ↓
            Pretrained CLIP
                   ↓
            Image Features
                   ↓
          CLIP Projection
                   ↓
        512-Dimensional Vector
                   ↓
             Normalize
                   ↓
         Cosine Similarity
                   ↓
          Similarity Score
```

This is the foundation of the Lostify AI matching engine.

---

# 21. What Week 01 Does NOT Claim

The Week 01 implementation does not yet:

- Detect objects using YOLO.
- Identify a person using face recognition.
- Extract OCR information.
- Match pets using specialized attributes.
- Search a real Lostify database.
- Use FAISS.
- Combine image + title + description.
- Produce final recovery decisions.

These are future stages of the AI pipeline.

The AI output will ultimately be a suggestion for human review, consistent with the project proposal.

---

# 22. Week 01 → Week 02

The next stage is:

```text
WEEK 01
Image
 ↓
CLIP
 ↓
Embedding
 ↓
Cosine Similarity
```

Then Week 02:

```text
WEEK 02

                    Query
                      ↓
          ┌───────────┴───────────┐
          ↓                       ↓
        Image                    Cases
          ↓                       ↓
        CLIP                   Embeddings
          └───────────┬───────────┘
                      ↓
                    FAISS
                      ↓
                  Similarity
                      ↓
                   Top-5
```

Then later:

```text
Image + Title + Description
              ↓
        Multimodal Matching
              ↓
          Top-5 Cases
```

---

# Week 01 Final Status

**Completed:** AI fundamentals + CLIP image embedding + normalization + cosine similarity.

**Immediate unfinished practical task:** build **query image → multiple existing case images → ranked Top-5 results**.

That is the correct bridge between Week 01 learning and the actual Lostify AI feature.
