# Lostify AI - Week 02
## Precomputed Image Embeddings and Similarity Search

### Week Objective

Week 02 improves the Week 01 image-similarity prototype by separating embedding generation from similarity search.

The main goal is to avoid running CLIP inference again for every stored case whenever a new query image is searched.

```text
Case images
    |
    v
CLIP image encoder
    |
    v
Normalized 512-dimensional embeddings
    |
    v
Saved .npy files
    |
    v
Load embeddings during search
    |
    v
Compare query with every case
    |
    v
Ranked similarity results
```

## 1. What Was Added in Week 02

### 1.1 Separate embedding generation

`generate_embeddings.py` processes the stored case images and saves each embedding in the `embeddings/` directory.

For each case, it:

1. Builds the image filename.
2. Checks whether the image exists.
3. Loads the image with PIL and converts it to RGB.
4. Runs the image through the pretrained CLIP vision model.
5. Projects the visual features to a 512-dimensional vector.
6. Normalizes the vector.
7. Saves it as a NumPy `.npy` file.

Example output file:

```text
embeddings/Case-01.npy
```

### 1.2 Reusable embedding storage

The generated vectors are stored on disk instead of being kept only in memory. This means the case embeddings can be reused across multiple searches.

The current embedding directory contains:

```text
Case-01.npy through Case-10.npy
```

Each file represents one case image and contains a normalized 512-dimensional vector.

### 1.3 Search using precomputed vectors

`similarity_search.py` loads the saved `.npy` files, generates an embedding only for the query image, and compares the query against the stored case vectors.

The search script:

1. Loads the CLIP model for the query image.
2. Reads all `.npy` files from `embeddings/`.
3. Loads the query image and generates its embedding.
4. Calculates cosine similarity between the query and every case.
5. Sorts results from highest similarity to lowest similarity.
6. Prints all cases and the top five matches.

## 2. Difference from Week 01

### Week 01 implementation

Week 01 used one script, `implementation/similarity_test.py`. It generated an embedding for the query and then generated a new embedding for every case during the same search.

```text
Query image -> CLIP -> Query embedding

Case 01 -> CLIP -> Case 01 embedding -> Compare
Case 02 -> CLIP -> Case 02 embedding -> Compare
...
Case 10 -> CLIP -> Case 10 embedding -> Compare
```

This approach is simple and useful for learning, but it repeats expensive model inference every time a search is performed.

### Week 02 implementation

Week 02 uses two stages:

```text
Stage 1: generate_embeddings.py
Case images -> CLIP -> Save case embeddings

Stage 2: similarity_search.py
Query image -> CLIP -> Query embedding
Saved case embeddings -> Load -> Compare and rank
```

| Area | Week 01 | Week 02 |
| --- | --- | --- |
| Number of scripts | One prototype script | Separate generation and search scripts |
| Case inference | Runs during every search | Runs once when embeddings are generated |
| Storage | Embeddings exist only during execution | Embeddings are saved as `.npy` files |
| Query inference | Generated during the search | Generated during the search |
| Search speed after setup | Slower because all cases use CLIP again | Faster because only the query uses CLIP |
| Data loading | Reads case image files directly | Reads precomputed vectors |
| Main purpose | Learn the similarity concept | Build a more reusable search pipeline |

## 3. Project Structure

```text
Week-02/
├── generate_embeddings.py   # Generate and save case vectors
├── similarity_search.py     # Search saved vectors using a query image
├── images/                  # Query and case images
├── embeddings/              # Saved 512-dimensional .npy vectors
└── output/day-01/           # Output area for experiment results
```

## 4. Technologies Used

- Python
- PyTorch
- Hugging Face Transformers
- OpenAI CLIP model: `openai/clip-vit-base-patch32`
- PIL/Pillow for image loading
- NumPy for saving and loading embeddings
- scikit-learn for cosine similarity

Install the required packages in the active Python environment:

```bash
pip install torch transformers pillow numpy scikit-learn
```

The first model run may download the CLIP model and processor from Hugging Face.

## 5. How to Run

Run commands from the Week 02 directory:

```bash
python generate_embeddings.py
python similarity_search.py
```

Run `generate_embeddings.py` again whenever a case image is added or replaced. Run `similarity_search.py` for each new query.

## 6. Expected Results

The search prints every case with its cosine similarity score and then prints the five highest-scoring cases.

```text
All Cases:
Case-03 -> 0.XXXX
Case-01 -> 0.XXXX
...

TOP 5 MATCHES
1. Case-03 -> 0.XXXX
2. Case-01 -> 0.XXXX
```

A higher score means the query and case embeddings point in more similar directions. The score is a ranking signal, not proof that two images show the same item.

## 7. Important Filename Note

File paths are case-sensitive on many systems. The current image folder contains `Query.jpg`, `case-06.jpg`, and `case-07.jpg`, while the scripts expect `images/query.jpg`, `images/Case-06.jpg`, and `images/Case-07.jpg`.

Before running the scripts, make the filenames consistent. For example:

```bash
mv images/Query.jpg images/query.jpg
mv images/case-06.jpg images/Case-06.jpg
mv images/case-07.jpg images/Case-07.jpg
```

The generator currently skips a missing case image and prints a warning. The search script expects the query image and the embeddings directory to exist.

## 8. Main Concepts Practiced

### Embedding generation

An embedding is a numerical representation of visual information. In this project, CLIP converts each image into 512 values.

### Normalization

Each embedding is normalized before it is saved or compared:

```python
image_features = image_features / image_features.norm(dim=-1, keepdim=True)
```

Normalization makes the vectors suitable for consistent cosine-similarity comparisons.

### Cosine similarity

Cosine similarity compares the direction of two vectors:

```text
similarity(A, B) = (A dot B) / (||A|| * ||B||)
```

### Precomputation

Precomputation moves repeated work into a separate preparation step. This makes repeated searches more efficient because the stored cases do not need to pass through CLIP for every query.

## 9. Week 02 Outcome

At the end of Week 02, Lostify AI has a two-stage image retrieval prototype:

```text
Images -> Precomputed embeddings -> Query embedding -> Cosine similarity -> Top 5 cases
```

This is a stronger foundation for a future Lostify AI backend, where embeddings could later be stored in a vector database and searched through an API.
