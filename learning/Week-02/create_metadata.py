import json

# Metadata is limited to details visible in the case images.
metadata = {
    "Case-01": {
        "image": "images/Case-01.jpg",
        "title": "Red and Black Travel Luggage",
        "category": "Luggage",
        "location": "Unknown",
        "description": "Several travel bags and suitcases, including a large red hard-shell suitcase and a gray duffel bag.",
        "notes": "The image shows luggage near a building; no exact location or owner details are visible."
    },
    "Case-02": {
        "image": "images/Case-02.jpg",
        "title": "White and Lavender Handbags",
        "category": "Bag",
        "location": "Unknown",
        "description": "A white handbag and a lavender quilted shoulder bag with chain straps.",
        "notes": "The image is a close-up of handbags; brand and ownership details are not confirmed."
    },
    "Case-03": {
        "image": "images/Case-03.jpg",
        "title": "Floral Bag and Pink Pouch",
        "category": "Bag",
        "location": "Unknown",
        "description": "A black bag and a pink pouch placed on a purple floral patterned surface.",
        "notes": "The image does not show identifying labels or a specific location."
    },
    "Case-04": {
        "image": "images/Case-04.jpg",
        "title": "Travel Bags with Hat",
        "category": "Luggage",
        "location": "Unknown",
        "description": "A black travel bag, brown leather bag, and light-colored hat arranged on a bed or sofa.",
        "notes": "The image shows indoor travel items; no exact location is visible."
    },
    "Case-05": {
        "image": "images/Case-05.jpg",
        "title": "Old Public Payphone",
        "category": "Electronics",
        "location": "Unknown",
        "description": "A weathered public payphone with a metal handset, keypad, and instruction panel.",
        "notes": "The image shows an old payphone but does not identify its location."
    },
    "Case-06": {
        "image": "images/case-06.jpg",
        "title": "Red and White Bicycle",
        "category": "Bicycle",
        "location": "Unknown",
        "description": "A red and white bicycle photographed on a paved outdoor surface.",
        "notes": "The frame is partly outside the image; no serial number is visible."
    },
    "Case-07": {
        "image": "images/case-07.jpg",
        "title": "Large Residential House",
        "category": "Property",
        "location": "Unknown",
        "description": "A large multi-story residential building photographed in bright outdoor light.",
        "notes": "The image contains a building and street scene but no identifiable address."
    },
    "Case-08": {
        "image": "images/Case-08.jpg",
        "title": "White and Brown Shopping Bags",
        "category": "Shopping Bag",
        "location": "Unknown",
        "description": "Multiple white and brown paper shopping bags arranged on a black metal surface.",
        "notes": "No store name, receipt, or location is clearly visible."
    },
    "Case-09": {
        "image": "images/Case-09.jpg",
        "title": "Colorful Shopping Bags",
        "category": "Shopping Bag",
        "location": "Unknown",
        "description": "A group of white and brown paper shopping bags on a black metal chair or table.",
        "notes": "The image does not show a readable store name or exact location."
    },
    "Case-10": {
        "image": "images/Case-10.jpg",
        "title": "Market Display of Handbags",
        "category": "Bag",
        "location": "Unknown",
        "description": "A market-style display of patterned bags, backpacks, beaded accessories, and handbags.",
        "notes": "The image shows a retail display; no individual item owner is identifiable."
    }
}

# Save to JSON file
with open("metadata.json", "w") as f:
    json.dump(metadata, f, indent=2)

print("✅ metadata.json created successfully!")