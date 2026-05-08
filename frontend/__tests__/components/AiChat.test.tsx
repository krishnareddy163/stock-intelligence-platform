import React from "react";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import AiChat from "@/components/AiChat";
import * as api from "@/services/api";

jest.mock("@/services/api", () => ({
  aiApi: {
    chat: jest.fn(),
  },
}));

const mockedChat = api.aiApi.chat as jest.Mock;

describe("AiChat", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("renders initial greeting message", () => {
    render(<AiChat userId="test-user" />);
    expect(screen.getByText(/Namaste/i)).toBeInTheDocument();
  });

  it("renders suggestion chips", () => {
    render(<AiChat userId="test-user" />);
    expect(screen.getByText("Best Nifty 50 stocks for 2025?")).toBeInTheDocument();
  });

  it("renders the header with AI advisor title", () => {
    render(<AiChat userId="test-user" />);
    expect(screen.getByText("AI Stock Advisor")).toBeInTheDocument();
  });

  it("renders Online status indicator", () => {
    render(<AiChat userId="test-user" />);
    expect(screen.getByText("Online")).toBeInTheDocument();
  });

  it("sends message on form submit and displays response", async () => {
    mockedChat.mockResolvedValueOnce({
      data: { response: "TCS is trading at ₹3912 with strong fundamentals." },
    });

    render(<AiChat userId="test-user" />);
    const input = screen.getByPlaceholderText(/ask about/i);
    await userEvent.type(input, "Is TCS a good buy?");
    await userEvent.keyboard("{Enter}");

    await waitFor(() => {
      expect(screen.getByText("Is TCS a good buy?")).toBeInTheDocument();
    });
    await waitFor(() => {
      expect(screen.getByText(/TCS is trading/)).toBeInTheDocument();
    });
    expect(mockedChat).toHaveBeenCalledWith("Is TCS a good buy?", "test-user", expect.any(Array));
  });

  it("sends message when suggestion chip is clicked", async () => {
    mockedChat.mockResolvedValueOnce({
      data: { response: "Here is a ₹1L growth portfolio suggestion..." },
    });

    render(<AiChat userId="test-user" />);
    await userEvent.click(screen.getByText("Build a ₹1L growth portfolio"));

    await waitFor(() => {
      expect(mockedChat).toHaveBeenCalledWith(
        "Build a ₹1L growth portfolio",
        "test-user",
        expect.any(Array)
      );
    });
  });

  it("shows error message when API call fails", async () => {
    mockedChat.mockRejectedValueOnce(new Error("Network error"));

    render(<AiChat userId="test-user" />);
    const input = screen.getByPlaceholderText(/ask about/i);
    await userEvent.type(input, "Test question");
    await userEvent.keyboard("{Enter}");

    await waitFor(() => {
      expect(screen.getByText(/orchestrator isn't running/i)).toBeInTheDocument();
    });
  });

  it("clears input after sending message", async () => {
    mockedChat.mockResolvedValueOnce({ data: { response: "Response text" } });

    render(<AiChat userId="test-user" />);
    const input = screen.getByPlaceholderText(/ask about/i) as HTMLInputElement;
    await userEvent.type(input, "Some question");
    await userEvent.keyboard("{Enter}");

    await waitFor(() => expect(input.value).toBe(""));
  });

  it("does not send empty messages", async () => {
    render(<AiChat userId="test-user" />);
    const input = screen.getByPlaceholderText(/ask about/i);
    await userEvent.click(input);
    await userEvent.keyboard("{Enter}");

    expect(mockedChat).not.toHaveBeenCalled();
  });

  it("disables input while loading", async () => {
    let resolveChat: (v: unknown) => void;
    mockedChat.mockReturnValueOnce(new Promise(r => { resolveChat = r; }));

    render(<AiChat userId="test-user" />);
    const input = screen.getByPlaceholderText(/ask about/i);
    await userEvent.type(input, "Loading test");
    await userEvent.keyboard("{Enter}");

    const sendButton = screen.getByRole("button", { name: /send/i });
    // While loading the button should be in a disabled-like state
    expect(sendButton).toBeDisabled();

    resolveChat!({ data: { response: "Done" } });
  });

  it("passes conversation history on follow-up messages", async () => {
    mockedChat
      .mockResolvedValueOnce({ data: { response: "TCS looks bullish." } })
      .mockResolvedValueOnce({ data: { response: "Infosys also looks good." } });

    render(<AiChat userId="test-user" />);
    const input = screen.getByPlaceholderText(/ask about/i);

    await userEvent.type(input, "TCS?");
    await userEvent.keyboard("{Enter}");
    await waitFor(() => screen.getByText("TCS looks bullish."));

    await userEvent.type(input, "Infosys?");
    await userEvent.keyboard("{Enter}");
    await waitFor(() => screen.getByText("Infosys also looks good."));

    const secondCall = mockedChat.mock.calls[1];
    const history = secondCall[2];
    expect(history.length).toBeGreaterThan(0);
    expect(history.some((m: { role: string }) => m.role === "user")).toBe(true);
  });
});
