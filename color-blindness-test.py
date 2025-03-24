import numpy as np
import cv2
from PIL import Image
from colorspacious import cspace_convert
import matplotlib.pyplot as plt

def analyze_colorblind_friendliness(image_path):
    # Load image
    img = cv2.imread(image_path)
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    
    # 1. Convert to various colorblind simulations
    # Using colorspacious for accurate CVD (color vision deficiency) simulation
    cvd_space = {"name": "sRGB1+CVD", "cvd_type": "deuteranomaly", "severity": 1.0}
    img_deuteranomaly = cspace_convert(img_rgb / 255.0, "sRGB1", cvd_space)
    
    cvd_space = {"name": "sRGB1+CVD", "cvd_type": "protanomaly", "severity": 1.0}
    img_protanomaly = cspace_convert(img_rgb / 255.0, "sRGB1", cvd_space)
    
    cvd_space = {"name": "sRGB1+CVD", "cvd_type": "tritanomaly", "severity": 1.0}
    img_tritanomaly = cspace_convert(img_rgb / 255.0, "sRGB1", cvd_space)
    
    # 2. Calculate color differentiation metrics
    # Extract dominant colors (simplified approach using k-means)
    pixels = img_rgb.reshape(-1, 3)
    pixels = np.float32(pixels)
    
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 200, 0.1)
    k = 5  # Number of dominant colors to extract
    _, labels, centers = cv2.kmeans(pixels, k, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS)
    
    # Convert back to uint8
    centers = np.uint8(centers)
    
    # Calculate contrast ratios between dominant colors
    contrast_issues = []
    for i in range(len(centers)):
        for j in range(i+1, len(centers)):
            contrast_ratio = calculate_contrast_ratio(centers[i], centers[j])
            if contrast_ratio < 3.0:  # Minimum recommended contrast for non-text elements
                contrast_issues.append((centers[i], centers[j], contrast_ratio))
    
    return {
        "original": img_rgb,
        "deuteranomaly": img_deuteranomaly,
        "protanomaly": img_protanomaly,
        "tritanomaly": img_tritanomaly,
        "contrast_issues": contrast_issues
    }

def calculate_contrast_ratio(color1, color2):
    # Convert RGB to luminance
    def get_luminance(rgb):
        rgb = rgb / 255.0
        rgb_linear = np.where(rgb <= 0.04045, rgb / 12.92, ((rgb + 0.055) / 1.055) ** 2.4)
        return 0.2126 * rgb_linear[0] + 0.7152 * rgb_linear[1] + 0.0722 * rgb_linear[2]
    
    l1 = get_luminance(color1)
    l2 = get_luminance(color2)
    
    # Calculate contrast ratio
    if l1 > l2:
        return (l1 + 0.05) / (l2 + 0.05)
    else:
        return (l2 + 0.05) / (l1 + 0.05)

def visualize_results(results):
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    
    axes[0, 0].imshow(results["original"])
    axes[0, 0].set_title("Original")
    axes[0, 0].axis("off")
    
    axes[0, 1].imshow(results["deuteranomaly"])
    axes[0, 1].set_title("Deuteranomaly (Green-blind)")
    axes[0, 1].axis("off")
    
    axes[1, 0].imshow(results["protanomaly"])
    axes[1, 0].set_title("Protanomaly (Red-blind)")
    axes[1, 0].axis("off")
    
    axes[1, 1].imshow(results["tritanomaly"])
    axes[1, 1].set_title("Tritanomaly (Blue-blind)")
    axes[1, 1].axis("off")
    
    plt.tight_layout()
    plt.show()
    
    # Print contrast issues
    if results["contrast_issues"]:
        print(f"Found {len(results['contrast_issues'])} problematic color combinations:")
        for i, (color1, color2, ratio) in enumerate(results["contrast_issues"]):
            print(f"  {i+1}. Colors {color1} and {color2}: Contrast ratio = {ratio:.2f}")
    else:
        print("No major contrast issues found between dominant colors.")

# Example usage
image_path = "your_image.jpg"
results = analyze_colorblind_friendliness(image_path)
visualize_results(results)
