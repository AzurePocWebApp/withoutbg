# Third-Party Licenses

This project uses the following third-party components:

## Depth Anything V2

**Repository**: https://github.com/DepthAnything/Depth-Anything-V2  
**License**: Apache License 2.0  
**Usage**: Used as part of the background removal pipeline (Small model only)

```
Copyright (c) 2024 Lihe Yang, Bingyi Kang, Zilong Huang, Zhen Zhao, Xiaogang Xu, Jiashi Feng, Hengshuang Zhao

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
```

## ISNet (Highly Accurate Dichotomous Image Segmentation)

**Repository**: https://github.com/xuebinqin/DIS  
**License**: Apache License 2.0  
**Usage**: Used as part of the background removal pipeline for segmentation

```
Copyright (c) 2022 Xuebin Qin, Hang Dai, Xiaobin Hu, Deng-Ping Fan, Ling Shao, Luc Van Gool

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
```

## Python Dependencies

The following Python packages are used by this project. Please refer to their respective licenses:

- **numpy**: BSD License
- **pillow**: PIL License (MIT-style)
- **onnxruntime**: MIT License
- **requests**: Apache License 2.0
- **click**: BSD License
- **tqdm**: MIT License
- **huggingface-hub**: Apache License 2.0

For complete license text of dependencies, use:
```bash
pip-licenses --format=markdown --output-file=DEPENDENCY_LICENSES.md
```

## Attribution Requirements

As required by the Apache 2.0 license, any distribution of this software must:

1. Include a copy of the Apache License 2.0 (LICENSE file)
2. Include this THIRD_PARTY_LICENSES.md file
3. Retain all copyright notices from the original authors
4. Include attribution to withoutbg.com in any public usage

## Model Weights Attribution

The ONNX model weights included in this distribution are derived from the above mentioned repositories and are subject to their respective licenses. Users redistributing these weights must comply with the original license terms.

---

For questions about licensing, contact: contact@withoutbg.com