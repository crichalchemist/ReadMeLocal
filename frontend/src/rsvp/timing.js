export const baseMsForWpm = (wpm) => Math.round(60000 / wpm);

export const tokenDelayMs = (token, baseMs) => {
  const punct = token.punct || "";
  if (punct === "," || punct === ";" || punct === ":") return baseMs + 150;
  if (punct === "." || punct === "!" || punct === "?") return baseMs + 300;
  return baseMs;
};
