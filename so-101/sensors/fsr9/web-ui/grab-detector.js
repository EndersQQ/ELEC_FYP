(function (root, factory) {
  const exported = factory();
  if (typeof module === "object" && module.exports) {
    module.exports = exported;
  } else {
    root.GrabDetector = exported.GrabDetector;
  }
})(typeof globalThis !== "undefined" ? globalThis : this, function () {
  "use strict";

  const DEFAULT_OPTIONS = Object.freeze({
    activeSensorPercent: 5,
    grabTotalPercent: 25,
    grabPeakPercent: 25,
    releaseTotalPercent: 12,
    releasePeakPercent: 8,
    enterFrames: 5,
    releaseFrames: 10,
  });

  class GrabDetector {
    constructor(options = {}) {
      this.options = { ...DEFAULT_OPTIONS, ...options };
      this.reset();
    }

    reset() {
      this.grabbing = false;
      this.enterCount = 0;
      this.releaseCount = 0;
    }

    update(sensorPercents) {
      const values = Array.from(sensorPercents, (value) =>
        Number.isFinite(value) && value > 0 ? value : 0
      );
      const totalPercent = values.reduce((total, value) => total + value, 0);
      const peakPercent = values.length > 0 ? Math.max(...values) : 0;
      const activeSensors = values.filter(
        (value) => value >= this.options.activeSensorPercent
      ).length;

      const grabEvidence =
        peakPercent >= this.options.grabPeakPercent ||
        (totalPercent >= this.options.grabTotalPercent && activeSensors >= 2);
      const releaseEvidence =
        totalPercent <= this.options.releaseTotalPercent &&
        peakPercent <= this.options.releasePeakPercent;

      if (!this.grabbing) {
        this.enterCount = grabEvidence ? this.enterCount + 1 : 0;
        if (this.enterCount >= this.options.enterFrames) {
          this.grabbing = true;
          this.enterCount = 0;
        }
      } else {
        this.releaseCount = releaseEvidence ? this.releaseCount + 1 : 0;
        if (this.releaseCount >= this.options.releaseFrames) {
          this.grabbing = false;
          this.releaseCount = 0;
        }
      }

      return {
        grabbing: this.grabbing,
        totalPercent,
        peakPercent,
        activeSensors,
      };
    }
  }

  return { GrabDetector, DEFAULT_OPTIONS };
});
