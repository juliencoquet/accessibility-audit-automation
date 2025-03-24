const colorBlind = require('color-blind');
const contrast = require('contrast-ratio');
const { createCanvas, loadImage } = require('canvas');
const kmeans = require('node-kmeans');

async function analyzeColorblindFriendliness(imagePath) {
    const image = await loadImage(imagePath);
    const canvas = createCanvas(image.width, image.height);
    const ctx = canvas.getContext('2d');
    ctx.drawImage(image, 0, 0);
    
    const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
    const pixels = [];
    
    // Extract pixels for k-means
    for (let i = 0; i < imageData.data.length; i += 4) {
        pixels.push([
            imageData.data[i],     // R
            imageData.data[i + 1], // G
            imageData.data[i + 2]  // B
        ]);
    }
    
    // Find dominant colors using k-means
    const k = 5;
    const result = await new Promise((resolve) => {
        kmeans.clusterize(pixels, { k }, (err, res) => {
            resolve(res);
        });
    });
    
    const dominantColors = result.map(cluster => cluster.centroid);
    
    // Check contrast between dominant colors
    const contrastIssues = [];
    for (let i = 0; i < dominantColors.length; i++) {
        for (let j = i + 1; j < dominantColors.length; j++) {
            const color1 = rgbToHex(dominantColors[i]);
            const color2 = rgbToHex(dominantColors[j]);
            const ratio = contrast(color1, color2);
            
            if (ratio < 3.0) {
                contrastIssues.push({
                    color1: dominantColors[i],
                    color2: dominantColors[j],
                    ratio
                });
            }
        }
    }
    
    // Simulate colorblindness on the entire image
    const simulations = {
        original: imageData,
        deuteranopia: simulateColorBlindness(imageData, 'deuteranopia'),
        protanopia: simulateColorBlindness(imageData, 'protanopia'),
        tritanopia: simulateColorBlindness(imageData, 'tritanopia')
    };
    
    return {
        simulations,
        contrastIssues
    };
}

function simulateColorBlindness(imageData, type) {
    const result = new Uint8ClampedArray(imageData.data.length);
    
    for (let i = 0; i < imageData.data.length; i += 4) {
        const r = imageData.data[i];
        const g = imageData.data[i + 1];
        const b = imageData.data[i + 2];
        const a = imageData.data[i + 3];
        
        const hex = rgbToHex([r, g, b]);
        const simulated = colorBlind[type](hex);
        const rgb = hexToRgb(simulated);
        
        result[i] = rgb.r;
        result[i + 1] = rgb.g;
        result[i + 2] = rgb.b;
        result[i + 3] = a;
    }
    
    return new ImageData(result, imageData.width, imageData.height);
}

function rgbToHex(rgb) {
    return '#' + rgb.map(v => {
        const hex = Math.round(v).toString(16);
        return hex.length === 1 ? '0' + hex : hex;
    }).join('');
}

function hexToRgb(hex) {
    const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
    return result ? {
        r: parseInt(result[1], 16),
        g: parseInt(result[2], 16),
        b: parseInt(result[3], 16)
    } : null;
}
