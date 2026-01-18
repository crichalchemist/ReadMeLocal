import { render, screen } from "@testing-library/react";
import App from "../App";

beforeEach(() => {
  global.fetch = jest.fn((url) => {
    if (url.endsWith("/api/settings")) {
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve({ library_path: "", rsvp: { wpm_default: 150 } }),
      });
    }
    if (url.endsWith("/api/library")) {
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve([]),
      });
    }
    return Promise.resolve({ ok: true, json: () => Promise.resolve({}) });
  });
});

afterEach(() => {
  global.fetch = undefined;
});

test("renders library heading", async () => {
  render(<App />);
  const headings = await screen.findAllByText(/Library/i);
  expect(headings.length).toBeGreaterThan(0);
});
