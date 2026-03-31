import React from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import "@testing-library/jest-dom";
import ErrorBanner from "@/components/ErrorBanner";
import SQLPreview from "@/components/SQLPreview";
import ResultTable from "@/components/ResultTable";
import QueryHistory from "@/components/QueryHistory";

describe("ErrorBanner", () => {
  it("renders error message", () => {
    render(<ErrorBanner message="Something went wrong" onDismiss={() => {}} />);
    expect(screen.getByText("Something went wrong")).toBeInTheDocument();
  });

  it("calls onDismiss when close button clicked", () => {
    const onDismiss = jest.fn();
    render(<ErrorBanner message="error" onDismiss={onDismiss} />);

    const closeBtn = screen.getByRole("button");
    fireEvent.click(closeBtn);
    expect(onDismiss).toHaveBeenCalledTimes(1);
  });
});

describe("SQLPreview", () => {
  it("renders generated SQL", () => {
    render(<SQLPreview sql="SELECT * FROM customers;" retrievedTables={[]} />);
    expect(screen.getByText("SELECT * FROM customers;")).toBeInTheDocument();
  });

  it("renders retrieved table badges", () => {
    render(
      <SQLPreview
        sql="SELECT 1;"
        retrievedTables={["customers", "orders"]}
      />
    );
    expect(screen.getByText("customers")).toBeInTheDocument();
    expect(screen.getByText("orders")).toBeInTheDocument();
  });

  it("renders copy button", () => {
    render(<SQLPreview sql="SELECT 1;" retrievedTables={[]} />);
    expect(screen.getByText("Copy")).toBeInTheDocument();
  });
});

describe("ResultTable", () => {
  it("renders table with data", () => {
    const result = {
      columns: ["name", "city"],
      rows: [
        ["Budi", "Jakarta"],
        ["Siti", "Bandung"],
      ],
      row_count: 2,
    };

    render(<ResultTable result={result} executionTimeMs={10} />);

    expect(screen.getByText("name")).toBeInTheDocument();
    expect(screen.getByText("city")).toBeInTheDocument();
    expect(screen.getByText("Budi")).toBeInTheDocument();
    expect(screen.getByText("Jakarta")).toBeInTheDocument();
    expect(screen.getByText("2 rows")).toBeInTheDocument();
    expect(screen.getByText("10ms")).toBeInTheDocument();
  });

  it("renders empty state when no rows", () => {
    const result = { columns: ["id"], rows: [], row_count: 0 };
    render(<ResultTable result={result} executionTimeMs={null} />);

    expect(screen.getByText(/returned no rows/)).toBeInTheDocument();
  });

  it("renders NULL values", () => {
    const result = {
      columns: ["name"],
      rows: [[null]],
      row_count: 1,
    };

    render(<ResultTable result={result} executionTimeMs={null} />);
    expect(screen.getByText("NULL")).toBeInTheDocument();
  });
});

describe("QueryHistory", () => {
  it("renders history items", () => {
    const items = [
      { id: 1, question: "Show customers", sql: "SELECT 1", success: true, timestamp: "2026-03-29T10:00:00Z" },
      { id: 2, question: "Show orders", sql: "SELECT 2", success: false, timestamp: "2026-03-29T11:00:00Z" },
    ];

    render(<QueryHistory items={items} onSelect={() => {}} />);

    expect(screen.getByText("Show customers")).toBeInTheDocument();
    expect(screen.getByText("Show orders")).toBeInTheDocument();
  });

  it("calls onSelect when item clicked", () => {
    const onSelect = jest.fn();
    const items = [
      { id: 1, question: "test query", sql: "SELECT 1", success: true, timestamp: "2026-03-29T10:00:00Z" },
    ];

    render(<QueryHistory items={items} onSelect={onSelect} />);
    fireEvent.click(screen.getByText("test query"));

    expect(onSelect).toHaveBeenCalledWith("test query");
  });

  it("renders empty state", () => {
    render(<QueryHistory items={[]} onSelect={() => {}} />);
    expect(screen.getByText(/No query history/)).toBeInTheDocument();
  });
});
