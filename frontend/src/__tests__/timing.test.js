import { baseMsForWpm, tokenDelayMs } from "../rsvp/timing";

test("tokenDelayMs adds punctuation pauses", () => {
  const base = baseMsForWpm(150);
  const token = { text: "world", punct: "." };
  expect(tokenDelayMs(token, base)).toBe(base + 300);
});
