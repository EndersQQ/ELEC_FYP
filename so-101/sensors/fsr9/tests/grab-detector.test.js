"use strict";

const assert = require("node:assert/strict");
const { GrabDetector } = require("../web-ui/grab-detector.js");

function repeat(detector, values, count) {
  let result;
  for (let index = 0; index < count; index += 1) {
    result = detector.update(values);
  }
  return result;
}

const detector = new GrabDetector();

assert.equal(repeat(detector, [0, 0, 0, 0, 0, 0, 0, 0, 0], 20).grabbing, false);
assert.equal(repeat(detector, [14, 13, 0, 0, 0, 0, 0, 0, 0], 4).grabbing, false);
assert.equal(detector.update([14, 13, 0, 0, 0, 0, 0, 0, 0]).grabbing, true);
assert.equal(repeat(detector, [0, 0, 0, 0, 0, 0, 0, 0, 0], 9).grabbing, true);
assert.equal(detector.update([0, 0, 0, 0, 0, 0, 0, 0, 0]).grabbing, false);

detector.reset();
assert.equal(repeat(detector, [26, 0, 0, 0, 0, 0, 0, 0, 0], 5).grabbing, true);

detector.reset();
assert.equal(repeat(detector, [5, 5, 5, 5, 0, 0, 0, 0, 0], 10).grabbing, false);

console.log("grab-detector tests passed");
