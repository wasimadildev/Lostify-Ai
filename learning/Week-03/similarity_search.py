"""Standalone Week 03 search experiment (Day 5 deliverable).

Runs the full pipeline end to end: CLIP embedding -> FAISS candidates ->
metadata filtering -> explainable ranking.

Examples:

    # Text-only
    python similarity_search.py --text "lost white persian cat in Islamabad" --query_type lost_pet

    # Image-only
    python similarity_search.py --image data/pets/PETS-01.jpg

    # Image + text
    python similarity_search.py \
        --image data/pets/PETS-01.jpg \
        --text "white cat with blue collar" \
        --location "Islamabad"
"""

import argparse
import time


def pretty_print(results, query):
    print("\n" + "=" * 66)
    print("  LOSTIFY AI - WEEK 03 SEARCH")
    print("=" * 66)
    print(f"  Query: {query}")
    print("=" * 66)

    for rank, r in enumerate(results, start=1):
        print(f"\n  {rank}. {r['case_id']}  [{r['case_type']} / {r['category']}]")
        print(f"     {r['title']}")
        print(f"     {r['location']}  |  lost {r.get('date_lost')}  |  {r['status']}")
        print(f"     final={r['final_score']}  "
              f"visual={r['visual_score']}  text={r['text_score']}  loc={r['location_score']}")


def main():
    parser = argparse.ArgumentParser(description="Lostify AI Week 03 search experiment")
    parser.add_argument("--image", help="path to a query image")
    parser.add_argument("--text", help="text description of the lost item")
    parser.add_argument("--query_type", choices=["lost_pet", "lost_item", "lost_person"],
                        help="restrict results to a case type")
    parser.add_argument("--location", help="city / area of the loss")
    parser.add_argument("--top_k", type=int, default=5)
    args = parser.parse_args()

    from engine import CLIPEngine
    engine = CLIPEngine()

    if args.image:
        with open(args.image, "rb") as f:
            image_bytes = f.read()
    else:
        image_bytes = None

    start = time.perf_counter()
    results = engine.search(
        image_bytes=image_bytes,
        text=args.text,
        query_type=args.query_type,
        location=args.location,
        top_k=args.top_k,
    )
    elapsed = (time.perf_counter() - start) * 1000

    pretty_print(results, {"image": args.image, "text": args.text,
                           "query_type": args.query_type, "location": args.location})
    print(f"\n  Retrieved in {elapsed:.0f} ms")


if __name__ == "__main__":
    main()