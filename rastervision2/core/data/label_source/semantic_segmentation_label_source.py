from typing import (List, Optional)

import numpy as np

from rastervision2.core.box import Box
from rastervision2.core.data.class_config import ClassConfig
from rastervision2.core.data import ActivateMixin
from rastervision2.core.data.label import SemanticSegmentationLabels
from rastervision2.core.data.label_source.label_source import (LabelSource)
from rastervision2.core.data.label_source.segmentation_class_transformer import (
    SegmentationClassTransformer)
from rastervision2.core.data.raster_source import RasterSource


class SemanticSegmentationLabelSource(ActivateMixin, LabelSource):
    """A read-only label source for semantic segmentation."""

    def __init__(self,
                 raster_source: RasterSource,
                 rgb_class_config: ClassConfig = None):
        """Constructor.

        Args:
            raster_source: (RasterSource) A raster source that returns a single channel
                raster with class_ids as values, or a 3 channel raster with
                RGB values that are mapped to class_ids using the rgb_class_map
            rgb_class_config: (ClassConfig) with color values filled in.
                Optional and used to
                transform RGB values to class ids. Only use if the raster source
                is RGB.
        """
        self.raster_source = raster_source
        self.class_transformer = None
        if rgb_class_config is not None:
            self.class_transformer = SegmentationClassTransformer(
                rgb_class_config)

    def enough_target_pixels(self, window: Box, target_count_threshold: int,
                             target_classes: List[int]) -> bool:
        """Given a window, answer whether the window contains enough pixels in
        the target classes.

        Args:
             window: The larger window from-which the sub-window will
                  be clipped.
             target_count_threshold:  Minimum number of target pixels.
             target_classes: The classes of interest.  The given
                  window is examined to make sure that it contains a
                  sufficient number of target pixels.
        Returns:
             True (the window does contain interesting pixels) or False.
        """
        raw_labels = self.raster_source.get_raw_chip(window)
        if self.class_transformer is not None:
            labels = self.class_transformer.rgb_to_class(raw_labels)
        else:
            labels = np.squeeze(raw_labels)

        target_count = 0
        for class_id in target_classes:
            target_count = target_count + (labels == class_id).sum()

        return target_count >= target_count_threshold

    def get_labels(self, window: Optional[Box] = None,
                   chip_size=1000) -> SemanticSegmentationLabels:
        """Get labels for a window.

        To avoid running out of memory, if window is None and defaults to using the full
        extent, a set of sub-windows of size chip_size are used which cover the full
        extent with no overlap.

        Args:
             window: Either None or a window given as a Box object. Uses full extent of
                scene if window is not provided.
             chip_size: size of sub-windows to use if full extent is used (in
                units of pixels)
        Returns:
             SemanticSegmentationLabels
        """
        labels = SemanticSegmentationLabels()
        windows = (self.raster_source.get_extent().get_windows(
            chip_size, chip_size) if window is None else [window])
        for w in windows:
            raw_labels = self.raster_source.get_raw_chip(w)
            label_arr = (np.squeeze(raw_labels)
                         if self.class_transformer is None else
                         self.class_transformer.rgb_to_class(raw_labels))
            labels.set_label_arr(w, label_arr)
        return labels

    def _subcomponents_to_activate(self):
        return [self.raster_source]

    def _activate(self):
        pass

    def _deactivate(self):
        pass
