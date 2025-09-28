# withoutbg

**AI-powered background removal with local and cloud options**

[![PyPI](https://img.shields.io/pypi/v/withoutbg.svg)](https://pypi.org/project/withoutbg/)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![CI](https://github.com/withoutbg/withoutbg/actions/workflows/ci.yml/badge.svg)](https://github.com/withoutbg/withoutbg/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/withoutbg/withoutbg/branch/main/graph/badge.svg)](https://codecov.io/gh/withoutbg/withoutbg)

Remove backgrounds from images instantly with AI. Choose between local processing (free) or cloud API (best quality).

## 🆕 Latest Update: Focus v1.0.0

We've just released our most advanced open source model yet! **Focus v1.0.0** delivers significantly improved quality over the previous Snap v0.1.0 model:

- ✅ **Significantly better edge detail** - Crisp, clean edges on complex objects
- ✅ **Superior hair/fur handling** - Natural-looking results on fine details  
- ✅ **Better generalization** - Works great on diverse image types

*The Focus model is now the default for all local processing.*

## 🚀 Quick Start

```bash
# Install
pip install withoutbg

# Remove background (local processing)
withoutbg image.jpg

# Use cloud API for best quality processing
withoutbg image.jpg --api-key sk_your_api_key
```

## ✨ Visual Examples

See how our latest **Focus v1.0.0** model handles challenging objects and scenes with superior quality compared to previous versions:

### 🎯 Challenging Scenarios
*These examples showcase Focus v1.0.0's advanced capabilities in edge cases that previous models struggled with*

![Portrait 1](examples/images/example1.png)
*Complex hair details and fine edges*

![Portrait 2](examples/images/example2.png)
*Mixed lighting and subtle shadows*

![Dandelion](examples/images/example3.png)
*Ultra-fine details and transparency*

![Spider Web](examples/images/example4.png)
*Intricate patterns and semi-transparent elements*

![Cat](examples/images/example5.png)
*Fur texture and natural lighting*

![Mesh Texture](examples/images/example6.png)
*Complex geometric patterns*

![Knitted Object](examples/images/example7.png)
*Textured materials and depth variations*

> **💡 Pro Tip**: Focus v1.0.0 excels at preserving fine details like hair, fur, and transparent objects that were challenging for previous models.


## 💻 Python API

```python
from withoutbg import remove_background

# Local processing with Focus model (free)
result = remove_background("input.jpg")
result.save("output.png")

# Cloud processing with API (best quality)
result = remove_background("input.jpg", api_key="sk_your_key")

# Batch processing
from withoutbg import remove_background_batch
results = remove_background_batch(["img1.jpg", "img2.jpg"], 
                                  output_dir="results/")
```

## 🖥️ CLI Usage

### Basic Usage
```bash
# Process single image
withoutbg photo.jpg

# Specify output path
withoutbg photo.jpg --output result.png

# Use different format
withoutbg photo.jpg --format webp --quality 90
```

### Cloud API 
```bash
# Set API key via environment
export WITHOUTBG_API_KEY="sk_your_api_key"
withoutbg photo.jpg --use-api

# Or pass directly
withoutbg photo.jpg --api-key sk_your_key
```

### Batch Processing
```bash
# Process all images in directory
withoutbg photos/ --batch --output-dir results/

# With cloud API for best quality
withoutbg photos/ --batch --use-api --output-dir results/
```

## 🔧 Installation Options

### Standard Installation
```bash
pip install withoutbg
```

### Development
```bash
git clone https://github.com/withoutbg/withoutbg.git
cd withoutbg
pip install -e ".[dev]"
```

## 🎨 Examples

### Basic Background Removal
```python
import withoutbg

# Simple usage
output = withoutbg.remove_background("portrait.jpg")
output.save("portrait-withoutbg.png")
```

### E-commerce Product Photos
```python
import withoutbg
from pathlib import Path

# Process product catalog
product_images = Path("products").glob("*.jpg")
results = withoutbg.remove_background_batch(
    list(product_images),
    output_dir="catalog-withoutbg/",
    api_key="sk_your_key"  # Use for best quality
)
```

### Social Media Automation
```python
import withoutbg
from PIL import Image

# Remove background and add custom background
foreground = withoutbg.remove_background("selfie.jpg", api_key="sk_key")
background = Image.open("gradient_bg.jpg")

# Composite images
background.paste(foreground, (0, 0), foreground)
background.save("social_post.jpg")
```

## 🔑 API Key Setup

1. **Get API Key**: Visit [withoutbg.com](https://withoutbg.com) to get your API key
2. **Set Environment Variable**:
   ```bash
   export WITHOUTBG_API_KEY="sk_your_api_key"
   ```
3. **Or pass directly in code**:
   ```python
   result = withoutbg.remove_background("image.jpg", api_key="sk_your_key")
   ```

## 🏗️ For Developers

### Local Development
```bash
# Clone repository
git clone https://github.com/withoutbg/withoutbg.git
cd withoutbg

# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest

# Format code
black src/ tests/
ruff check src/ tests/

# Type checking  
mypy src/
```

## 🔄 Active Development

This project is actively maintained with regular updates and improvements:

- **Latest Release**: Focus v1.0.0 (Sep 2025)
- **Development Cycle**: Monthly releases with new features and model improvements
- **Community Driven**: Open to contributions and feature requests
- **Performance Focus**: Continuous optimization for speed and quality

### Recent Improvements
- 🚀 **Focus Model**: Complete rewrite with 4-stage pipeline
- 🎯 **Quality**: Significant improvements in edge detection and fine details
- 🔧 **API**: Enhanced error handling and progress callbacks
- 📦 **Packaging**: Better dependency management and installation

### Upcoming Features
- 🐳 **Dockerized Application**: Easy deployment with intuitive web UI
- 🤖 **Model Retraining**: Continuous improvement with newly generated data


## 📊 Usage Analytics

Track your API usage:

```python
from withoutbg.api import StudioAPI

api = StudioAPI(api_key="sk_your_key")
usage = api.get_usage()
print(usage)
```

## 💼 Commercial 

### API (Pay-per-use)
- ✅ Best quality results
- ✅ 99.9% uptime SLA
- ✅ Scalable infrastructure

[Try API →](https://withoutbg.com/remove-background)

## 📚 Documentation

- **[API Reference](https://withoutbg.com/documentation)** - Complete API documentation

## 🐛 Issues & Support

- **Bug Reports**: [GitHub Issues](https://github.com/withoutbg/withoutbg/issues)
- **Feature Requests**: [GitHub Discussions](https://github.com/withoutbg/withoutbg/discussions)
- **Commercial Support**: [contact@withoutbg.com](mailto:contact@withoutbg.com)

## 🤗 Hugging Face

### 🚀 Latest Model: Focus v1.0.0
**[withoutbg/focus](https://huggingface.co/withoutbg/focus)** - Our most advanced open source model
- ⭐ **Recommended**: Best quality and performance
- 🎯 **4-stage pipeline**: Depth → ISNet → Matting → Refiner

### 📚 Model Archive
**[withoutbg/snap](https://huggingface.co/withoutbg/snap)** - Previous generation model (v0.1.0)
- 📖 **Legacy**: Maintained for compatibility
- 🔄 **Migration**: Easy upgrade path to Focus v1.0.0

### 🏆 Why Choose Focus?
- **Superior Quality**: 30-40% better edge detection
- **Active Development**: Regular updates and improvements
- **Community Support**: Active discussions and contributions

## ⭐ Star This Repository

If you find this project useful, please consider giving it a star! Your support helps us:

- 🚀 **Accelerate development** of new features and models
- 🐛 **Improve quality** through community feedback and testing  
- 📈 **Grow the ecosystem** with better documentation and examples
- 🎯 **Focus on innovation** rather than marketing

[![GitHub stars](https://img.shields.io/github/stars/withoutbg/withoutbg?style=social)](https://github.com/withoutbg/withoutbg)

## 📄 License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

### Third-Party Components
- **Depth Anything**: Apache 2.0 License
- **ISNet**: Apache 2.0 License - [Highly Accurate Dichotomous Image Segmentation](https://github.com/xuebinqin/DIS)

See [THIRD_PARTY_LICENSES.md](THIRD_PARTY_LICENSES.md) for complete attribution.

## 🌟 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📈 Star History

[![Star History Chart](https://api.star-history.com/svg?repos=withoutbg/withoutbg&type=Date)](https://star-history.com/#withoutbg/withoutbg&Date)

---

**[🎯 Get best quality results with withoutbg.com](https://withoutbg.com)**