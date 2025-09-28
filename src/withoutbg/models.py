"""Local model implementations."""

import io
from pathlib import Path
from typing import Any, Optional, Union

import numpy as np
import onnxruntime as ort  # type: ignore
from huggingface_hub import hf_hub_download
from PIL import Image

from .exceptions import ModelNotFoundError, WithoutBGError


class OpenSourceModel:
    """Local ONNX-based background removal model (Open Source tier)."""

    def __init__(
        self,
        depth_model_path: Optional[Union[str, Path]] = None,
        isnet_model_path: Optional[Union[str, Path]] = None,
        matting_model_path: Optional[Union[str, Path]] = None,
        refiner_model_path: Optional[Union[str, Path]] = None,
    ):
        """Initialize the Open Source model with 4-stage pipeline.

        Args:
            depth_model_path: Path to Depth Anything V2 ONNX model. If None,
                downloads from HF.
            isnet_model_path: Path to ISNet segmentation ONNX model. If None, downloads from HF.
            matting_model_path: Path to Matting ONNX model. If None, downloads from HF.
            refiner_model_path: Path to Refiner ONNX model. If None, downloads from HF.
        """
        self.depth_model_path = depth_model_path or self._get_default_depth_model_path()
        self.isnet_model_path = (
            isnet_model_path or self._get_default_isnet_model_path()
        )
        self.matting_model_path = (
            matting_model_path or self._get_default_matting_model_path()
        )
        self.refiner_model_path = (
            refiner_model_path or self._get_default_refiner_model_path()
        )


        self.depth_session = None
        self.isnet_session = None
        self.matting_session = None
        self.refiner_session = None

        self._load_models()

    def _get_default_depth_model_path(self) -> Path:
        """Get path to Depth Anything V2 model from Hugging Face."""
        return self._download_from_hf(
            "depth_anything_v2_vits_slim.onnx", "Depth Anything V2 model"
        )

    def _get_default_isnet_model_path(self) -> Path:
        """Get path to ISNet segmentation model from Hugging Face."""
        return self._download_from_hf("isnet.onnx", "ISNet segmentation model")

    def _get_default_matting_model_path(self) -> Path:
        """Get path to Matting model from Hugging Face."""
        return self._download_from_hf("focus_matting_1.0.0.onnx", "Focus matting model")

    def _get_default_refiner_model_path(self) -> Path:
        """Get path to Refiner model from Hugging Face."""
        return self._download_from_hf("focus_refiner_1.0.0.onnx", "Focus refiner model")

    def _download_from_hf(self, filename: str, model_name: str) -> Path:
        """Download model from Hugging Face Hub with caching.

        Args:
            filename: Name of the model file to download
            model_name: Human-readable name for error messages

        Returns:
            Path to the downloaded model file

        Raises:
            ModelNotFoundError: If download fails or HF Hub is not available
        """

        try:
            # First try to get from cache
            try:
                model_path = hf_hub_download(
                    repo_id="withoutbg/focus",
                    filename=filename,
                    cache_dir=None,  # Use default cache
                    local_files_only=True,  # Only check cache first
                )
                return Path(model_path)
            except Exception:
                # If not in cache, download it
                print(f"Downloading {model_name} from Hugging Face...")
                model_path = hf_hub_download(
                    repo_id="withoutbg/focus",
                    filename=filename,
                    cache_dir=None,  # Use default cache
                    local_files_only=False,
                )
                print(f"✓ {model_name} downloaded successfully")
                return Path(model_path)

        except Exception as e:
            raise ModelNotFoundError(
                f"Failed to download {model_name} from Hugging Face: {str(e)}\n"
                f"You can manually download models from: "
                f"https://huggingface.co/withoutbg/focus"
            ) from e

    def _load_models(self) -> None:
        """Load all four ONNX models."""
        try:
            # Configure ONNX Runtime for optimal performance
            providers = ["CPUExecutionProvider"]
            if ort.get_available_providers():
                # Prefer GPU if available
                available = ort.get_available_providers()
                if "CUDAExecutionProvider" in available:
                    providers = ["CUDAExecutionProvider", "CPUExecutionProvider"]

            # Load Depth Anything V2 model
            self.depth_session = ort.InferenceSession(
                str(self.depth_model_path), providers=providers
            )

            # Load ISNet segmentation model
            self.isnet_session = ort.InferenceSession(
                str(self.isnet_model_path), providers=providers
            )

            # Load Matting model
            self.matting_session = ort.InferenceSession(
                str(self.matting_model_path), providers=providers
            )

            # Load Refiner model
            self.refiner_session = ort.InferenceSession(
                str(self.refiner_model_path), providers=providers
            )

        except Exception as e:
            raise ModelNotFoundError(f"Failed to load models: {str(e)}") from e

    def _constrain_to_multiple_of(
        self,
        x: float,
        ensure_multiple_of: int,
        min_val: int = 0,
        max_val: Optional[int] = None,
    ) -> int:
        """Constrain value to be multiple of ensure_multiple_of."""
        y = int(np.round(x / ensure_multiple_of) * ensure_multiple_of)

        if max_val is not None and y > max_val:
            y = int(np.floor(x / ensure_multiple_of) * ensure_multiple_of)

        if y < min_val:
            y = int(np.ceil(x / ensure_multiple_of) * ensure_multiple_of)

        return y

    def _get_new_size(
        self,
        orig_width: int,
        orig_height: int,
        target_width: int,
        target_height: int,
        ensure_multiple_of: int,
    ) -> tuple[int, int]:
        """Calculate new size maintaining aspect ratio."""
        scale_height = target_height / orig_height
        scale_width = target_width / orig_width

        if scale_width > scale_height:
            scale_height = scale_width
        else:
            scale_width = scale_height

        new_height = self._constrain_to_multiple_of(
            scale_height * orig_height, ensure_multiple_of, min_val=target_height
        )
        new_width = self._constrain_to_multiple_of(
            scale_width * orig_width, ensure_multiple_of, min_val=target_width
        )

        return new_width, new_height

    def _normalize_image(self, img: np.ndarray) -> np.ndarray:
        """Normalize image with ImageNet statistics."""
        mean = np.array([0.485, 0.456, 0.406])
        std = np.array([0.229, 0.224, 0.225])
        result: np.ndarray = (img - mean) / std
        return result

    def _prepare_image(self, img: np.ndarray) -> np.ndarray:
        """Prepare image for model input."""
        img = np.transpose(img, (2, 0, 1))
        img = np.ascontiguousarray(img, dtype=np.float32)
        return img

    def transform_for_isnet(self, im: np.ndarray) -> np.ndarray:
        """Transform image for ISNet model preprocessing.
        
        Args:
            im: Input image as numpy array (H, W, C) with values in [0, 255]
            
        Returns:
            Preprocessed image ready for ISNet model inference
        """
        # Convert numpy array to PIL Image for resizing
        pil_image = Image.fromarray(im.astype(np.uint8))
        
        # Resize to 1024x1024 using PIL
        pil_image = pil_image.resize((1024, 1024), Image.Resampling.LANCZOS)
        
        # Convert back to numpy array
        im = np.array(pil_image, dtype=np.float32)

        # Normalize to [0, 1]
        im = im / 255.0
        
        # Apply ISNet-specific normalization
        mean = np.array([0.5, 0.5, 0.5])
        std = np.array([1.0, 1.0, 1.0])
        im = (im - mean) / std

        # Convert to channel-first format (C, H, W)
        im = np.transpose(im, (2, 0, 1))

        # Convert to float32
        im = im.astype(np.float32)

        # Add batch dimension (1, C, H, W)
        im = np.expand_dims(im, axis=0)

        return im

    def _isnet_stage(self, image: Image.Image) -> np.ndarray:
        """
        ISNet segmentation stage for background removal.
        
        Parameters:
        - image (PIL.Image.Image): The input RGB PIL Image.
        
        Returns:
        - np.ndarray: Alpha mask from ISNet segmentation (H, W) with values in [0, 1].
        """
        # Convert PIL image to numpy array
        img_array = np.array(image)
        
        # Transform for ISNet
        processed_img = self.transform_for_isnet(img_array)
        
        # Run inference using ISNet
        assert self.isnet_session is not None, "ISNet model not loaded"
        
        # Get the actual input name from the model
        input_name = self.isnet_session.get_inputs()[0].name
        ort_inputs = {input_name: processed_img}  # type: ignore[unreachable]
        ort_outs = self.isnet_session.run(None, ort_inputs)
        alpha_output = ort_outs[0]
        
        # Process output: remove batch dimension
        alpha_output = alpha_output.squeeze(0)
        if len(alpha_output.shape) == 3:
            alpha_output = alpha_output[0]
        
        # Keep values in [0, 1] range for further processing
        alpha_output = np.clip(alpha_output, 0, 1).astype(np.float32)
        
        return alpha_output

    def _preprocess_for_depth(
        self,
        image: Image.Image,
        target_width: int,
        target_height: int,
        ensure_multiple_of: int = 1,
        interpolation_method: int = Image.Resampling.LANCZOS,
    ) -> np.ndarray:
        """
        Transforms an input image to prepare it for depth estimation by
        resizing, normalizing, and formatting it.

        Parameters:
        - image (PIL.Image.Image): The input image as a PIL Image object.
        - target_width (int): The target width for resizing the image.
        - target_height (int): The target height for resizing the image.
        - ensure_multiple_of (int, optional): Ensures the dimensions of the
          resized image are multiples of this value. Defaults to 1.
        - interpolation_method (int, optional): The interpolation method to
          use for resizing. Defaults to Image.Resampling.LANCZOS.

        Returns:
        - np.ndarray: The transformed image, normalized, and with the correct
          dimensions and format for model input.
        """
        # Calculate new size
        new_width, new_height = self._get_new_size(
            image.width, image.height, target_width, target_height, ensure_multiple_of
        )

        # Resize image
        resized_pil = image.resize(
            (new_width, new_height), resample=Image.Resampling(interpolation_method)
        )
        resized_image = np.array(resized_pil).astype(np.float32) / 255.0

        # Normalize image
        normalized_image = self._normalize_image(resized_image)

        # Prepare image
        prepared_image = self._prepare_image(normalized_image)

        # Add batch dimension
        prepared_image_batched: np.ndarray = np.expand_dims(prepared_image, axis=0)

        return prepared_image_batched.astype(np.float32)

    def _estimate_depth(
        self,
        image: Image.Image,
        target_width: int = 518,
        target_height: int = 518,
        ensure_multiple_of: int = 14,
        interpolation_method: int = Image.Resampling.BICUBIC,
    ) -> Image.Image:
        """
        Stage 1: Depth estimation using Depth Anything V2 model.

        Parameters:
        - image (PIL.Image.Image): The input RGB PIL Image.
        - target_width (int, optional): Target width for preprocessing. Defaults to 518.
        - target_height (int, optional): Target height for preprocessing.
          Defaults to 518.
        - ensure_multiple_of (int, optional): Ensures dimensions are multiples
          of this value. Defaults to 14.
        - interpolation_method (int, optional): PIL interpolation method.
          Defaults to Image.Resampling.BICUBIC.

        Returns:
        - PIL.Image.Image: The inverse depth map as a grayscale PIL Image (0-255 range).
        """
        # Transform image
        img_array = self._preprocess_for_depth(
            image, target_width, target_height, ensure_multiple_of, interpolation_method
        )

        # Inference using ONNX
        assert self.depth_session is not None, "Depth model not loaded"
        ort_inputs = {"image": img_array}  # type: ignore[unreachable]
        ort_outs = self.depth_session.run(None, ort_inputs)
        depth = ort_outs[0]

        # Rescale depth map to 0-255 (inverse depth)
        depth = (depth - depth.min()) / (depth.max() - depth.min()) * 255.0
        depth = depth.astype(np.uint8)
        depth = depth.squeeze(0)

        # From tensor to image
        depth_image = Image.fromarray(depth)

        return depth_image

    def _matting_stage(
        self, rgb_image: Image.Image, depth_image: Image.Image, isnet_mask: np.ndarray
    ) -> Image.Image:
        """
        Stage 2: Matting using RGBD + ISNet mask input (RGB + inverse depth + ISNet mask concatenated).

        Parameters:
        - rgb_image (PIL.Image.Image): The original RGB image.
        - depth_image (PIL.Image.Image): The inverse depth map from stage 1.
        - isnet_mask (np.ndarray): The ISNet segmentation mask from stage 1.5.

        Returns:
        - PIL.Image.Image: Alpha channel (A1) as grayscale PIL Image.
        """
        # Resize all inputs to 256x256 for matting model
        rgb_resized = rgb_image.resize((256, 256), Image.Resampling.LANCZOS)
        depth_resized = depth_image.resize((256, 256), Image.Resampling.LANCZOS)
        
        # Resize ISNet mask to 256x256 using PIL
        isnet_mask_pil = Image.fromarray((isnet_mask * 255).astype(np.uint8), mode='L')
        isnet_mask_resized = np.array(isnet_mask_pil.resize((256, 256), Image.Resampling.LANCZOS), dtype=np.float32) / 255.0

        # Convert to numpy arrays and normalize to [0, 1]
        rgb_array = np.array(rgb_resized, dtype=np.float32) / 255.0
        depth_array = np.array(depth_resized, dtype=np.float32) / 255.0

        # Ensure depth is single channel (grayscale)
        if len(depth_array.shape) == 3:
            depth_array = depth_array[:, :, 0]

        # Concatenate RGB + depth + ISNet mask to create 5-channel input
        rgbd_mask_array = np.concatenate(
            [
                rgb_array,
                np.expand_dims(depth_array, axis=2),
                np.expand_dims(isnet_mask_resized, axis=2),
            ],
            axis=2,
        )

        # Prepare for model: transpose to CHW format and add batch dimension
        rgbd_mask_tensor = np.transpose(rgbd_mask_array, (2, 0, 1))
        rgbd_mask_tensor = np.expand_dims(rgbd_mask_tensor, axis=0)
        rgbd_mask_tensor = np.ascontiguousarray(rgbd_mask_tensor, dtype=np.float32)

        # Run inference through matting model
        assert self.matting_session is not None, "Matting model not loaded"
        
        # Get the actual input name from the model
        input_name = self.matting_session.get_inputs()[0].name
        ort_inputs = {input_name: rgbd_mask_tensor}  # type: ignore[unreachable]
        ort_outs = self.matting_session.run(None, ort_inputs)
        alpha_output = ort_outs[0]

        # Process output: remove batch dimension and convert to grayscale image
        alpha_output = alpha_output.squeeze(0)
        if len(alpha_output.shape) == 3:
            alpha_output = alpha_output[0]

        # Normalize to 0-255 range
        alpha_output = np.clip(alpha_output * 255.0, 0, 255).astype(np.uint8)

        # Convert to PIL Image
        alpha_image = Image.fromarray(alpha_output, mode="L")

        return alpha_image

    def _calculate_refiner_size(self, original_size: tuple[int, int]) -> tuple[int, int]:
        """Calculate optimal size for refiner model (max 1024px on bigger side)."""
        width, height = original_size
        max_size = 1024
        
        # If both dimensions are already <= 1024, no resizing needed
        if width <= max_size and height <= max_size:
            return original_size
        
        # Calculate scale factor to make the bigger side = 1024
        scale = max_size / max(width, height)
        new_width = int(width * scale)
        new_height = int(height * scale)
        
        return (new_width, new_height)

    def _refiner_stage(
        self, rgb_image: Image.Image, alpha1: Image.Image
    ) -> Image.Image:
        """
        Stage 3: Refine alpha channel using RGB + alpha concatenated input.
        
        Optimizes performance by resizing large images to max 1024px on the bigger side
        for inference, then upscaling the result back to original resolution.

        Parameters:
        - rgb_image (PIL.Image.Image): The original RGB image.
        - alpha1 (PIL.Image.Image): The alpha channel from matting stage.

        Returns:
        - PIL.Image.Image: Refined alpha channel (A2) with high detail and resolution.
        """
        # Get original image size
        original_size = rgb_image.size
        
        # Calculate optimal size for refiner model (max 1024px on bigger side)
        refiner_size = self._calculate_refiner_size(original_size)
        
        # Resize RGB image for refiner model if needed
        if refiner_size != original_size:
            rgb_resized = rgb_image.resize(refiner_size, Image.Resampling.LANCZOS)
        else:
            rgb_resized = rgb_image

        # Scale RGB image to [0, 1]
        rgb_array = np.array(rgb_resized, dtype=np.float32) / 255.0

        # Resize alpha to match the refiner input size
        alpha_resized = alpha1.resize(refiner_size, Image.Resampling.LANCZOS)

        # Convert to array and scale to [0, 1]
        alpha_array = np.array(alpha_resized, dtype=np.float32) / 255.0

        # Ensure alpha is single channel
        if len(alpha_array.shape) == 3:
            alpha_array = alpha_array[:, :, 0]

        # Concatenate RGB + alpha to create 4-channel input
        rgba_array = np.concatenate(
            [
                rgb_array,
                np.expand_dims(alpha_array, axis=2),
            ],
            axis=2,
        )

        # Prepare for model: transpose to CHW format and add batch dimension
        input_tensor = np.transpose(rgba_array, (2, 0, 1))
        input_tensor = np.expand_dims(input_tensor, axis=0)
        input_tensor = np.ascontiguousarray(input_tensor, dtype=np.float32)

        # Run inference through refiner model
        assert self.refiner_session is not None, "Refiner model not loaded"
        
        # Get the actual input name from the model
        input_name = self.refiner_session.get_inputs()[0].name
        ort_inputs = {input_name: input_tensor}  # type: ignore[unreachable]
        ort_outs = self.refiner_session.run(None, ort_inputs)
        alpha_output = ort_outs[0]

        # Process output: remove batch dimension
        alpha_output = alpha_output.squeeze(0)
        if len(alpha_output.shape) == 3:
            alpha_output = alpha_output[0]

        # Normalize to 0-255 range
        alpha_output = np.clip(alpha_output * 255.0, 0, 255).astype(np.uint8)

        # Convert to PIL Image
        refined_alpha = Image.fromarray(alpha_output, mode="L")
        
        # Resize refined alpha back to original resolution if it was downscaled
        if refiner_size != original_size:
            refined_alpha = refined_alpha.resize(original_size, Image.Resampling.LANCZOS)

        return refined_alpha

    def estimate_alpha(self, image: Image.Image, progress_callback: Optional[callable] = None) -> Image.Image:
        """
        Full 4-stage pipeline: Depth Anything V2 -> ISNet -> Matting -> Refiner.

        Parameters:
        - image (PIL.Image.Image): Input RGB image.
        - progress_callback: Optional callback function for progress updates (progress)

        Returns:
        - PIL.Image.Image: Final refined alpha channel.
        """
        if progress_callback:
            progress_callback(0.0)
        
        # Stage 1: Depth estimation
        if progress_callback:
            progress_callback(0.2)
        depth_map = self._estimate_depth(image)

        # Stage 1.5: ISNet segmentation
        if progress_callback:
            progress_callback(0.6)
        isnet_mask = self._isnet_stage(image)

        # Stage 2: Matting (RGB + Depth + ISNet mask -> A1)
        if progress_callback:
            progress_callback(0.7)
        alpha1 = self._matting_stage(image, depth_map, isnet_mask)

        # Stage 3: Refiner (RGB + alpha -> A2)
        if progress_callback:
            progress_callback(0.8)
        alpha2 = self._refiner_stage(image, alpha1)

        if progress_callback:
            progress_callback(1.0)

        return alpha2

    def estimate_alpha_isnet(self, image: Image.Image) -> Image.Image:
        """
        Single-stage ISNet-based alpha estimation.
        
        Parameters:
        - image (PIL.Image.Image): Input RGB image.
        
        Returns:
        - PIL.Image.Image: Alpha channel from ISNet segmentation.
        """
        isnet_mask = self._isnet_stage(image)
        
        # Convert numpy array to PIL Image
        alpha_output = np.clip(isnet_mask * 255.0, 0, 255).astype(np.uint8)
        alpha_image = Image.fromarray(alpha_output, mode="L")
        
        return alpha_image

    def remove_background(
        self, input_image: Union[str, Path, Image.Image, bytes], progress_callback: Optional[callable] = None, **kwargs: Any
    ) -> Image.Image:
        """Remove background from image using local Open Source model.

        Args:
            input_image: Input image
            progress_callback: Optional callback function for progress updates (progress)
            **kwargs: Additional arguments (unused for Open Source model)

        Returns:
            PIL Image with background removed
        """
        # Load image
        if isinstance(input_image, (str, Path)):
            with Image.open(input_image) as img:
                image = img.copy()
        elif isinstance(input_image, bytes):
            with Image.open(io.BytesIO(input_image)) as img:
                image = img.copy()
        elif isinstance(input_image, Image.Image):
            image = input_image.copy()
        else:
            raise WithoutBGError(f"Unsupported input type: {type(input_image)}")

        # Convert to RGB if needed (model expects RGB only)
        if image.mode != "RGB":
            image = image.convert("RGB")

        original_size = image.size

        try:
            # Run 3-stage pipeline to get final alpha channel
            alpha_channel = self.estimate_alpha(image, progress_callback=progress_callback)

            # Resize alpha to original image size
            alpha_resized = alpha_channel.resize(
                original_size, Image.Resampling.LANCZOS
            )

            # Convert original image to RGBA
            if image.mode != "RGBA":
                image = image.convert("RGBA")

            # Apply alpha channel to create final RGBA image
            image_array = np.array(image)
            alpha_array = np.array(alpha_resized)

            # Replace alpha channel
            image_array[:, :, 3] = alpha_array

            result_image = Image.fromarray(image_array, "RGBA")

            return result_image

        except Exception as e:
            raise WithoutBGError(f"Model inference failed: {str(e)}") from e
