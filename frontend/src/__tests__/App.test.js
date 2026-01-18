import { render, screen } from "@testing-library/react";
import App from "../App";

test("renders library heading", () => {
  render(<App />);
  expect(screen.getByText(/Library/i)).toBeTruthy();
});
