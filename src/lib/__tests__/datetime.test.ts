import { describe, expect, it } from "vitest";
import { parseApiDate } from "../datetime";

describe("parseApiDate", () => {
  it("treats SQLite timestamps without a suffix as UTC", () => {
    expect(parseApiDate("2026-07-19 08:09:10").toISOString()).toBe("2026-07-19T08:09:10.000Z");
  });

  it("preserves explicit ISO timezone offsets", () => {
    expect(parseApiDate("2026-07-19T16:09:10+08:00").toISOString()).toBe("2026-07-19T08:09:10.000Z");
  });
});
