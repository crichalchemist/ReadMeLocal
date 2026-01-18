import { fireEvent, render, screen } from "@testing-library/react";
import App from "../App";

afterEach(() => {
  global.fetch = undefined;
});

test("highlights current paragraph", async () => {
  global.fetch = jest.fn((url) => {
    if (url.endsWith("/api/library")) {
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve([{ id: "book-1", title: "Test Book" }]),
      });
    }
    if (url.endsWith("/api/books/book-1")) {
      return Promise.resolve({
        ok: true,
        json: () =>
          Promise.resolve({
            title: "Test Book",
            tokens: [{ text: "Hello", paragraph_index: 0 }],
            paragraphs: ["Hello world."],
          }),
      });
    }
    return Promise.resolve({ ok: false, json: () => Promise.resolve({}) });
  });

  render(<App />);

  const bookButton = await screen.findByText("Test Book");
  fireEvent.click(bookButton);

  const paragraph = await screen.findByText("Hello world.");
  expect(paragraph.classList.contains("active")).toBe(true);
});
