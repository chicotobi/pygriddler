#pragma once

#include <vector>
#include <cstdint>

namespace nonogram
{

    // Type aliases for clarity
    using LineArray = std::vector<int8_t>;                              // A single line of colors
    using PossibleLines = std::vector<LineArray>;                       // Collection of possible lines
    using ColorPossible = std::vector<std::vector<std::vector<float>>>; // [y][x][color]

    // Structure to hold line constraints
    struct LineConstraints
    {
        std::vector<int> block_lengths;
        std::vector<int> block_colors;
    };

    // Structure to hold line generation state
    struct LineState
    {
        PossibleLines possible_lines;
        bool generated;
        int count;
    };

    // Main solver class
    class NonogramSolver
    {
    public:
        // Constructor
        NonogramSolver(int width, int height, int n_colors,
                       const std::vector<LineConstraints> &h_constraints,
                       const std::vector<LineConstraints> &v_constraints);

        // Initialize solver - generate initial possible lines
        void initialize(int limit_generate);

        // Main solve function - returns solved grid
        // Returns: vector of size height*width with color indices (-1 for unsolved)
        std::vector<int> solve(bool verbose = false);

        // Get current solution state (for visualization)
        std::vector<int> get_current_state() const;

    private:
        // Core solver iteration
        bool solve_iteration();

        // Generate possible lines for a constraint (recursive implementation)
        void generate_lines_recursive(int length,
                                      const std::vector<int> &block_lengths,
                                      const std::vector<int> &block_colors,
                                      int previous_color,
                                      int pos,
                                      LineArray current,
                                      PossibleLines &result);

        // Count lines recursively
        int count_lines_recursive(int length,
                                  const std::vector<int> &block_lengths,
                                  const std::vector<int> &block_colors,
                                  int previous_color);

        // Generate possible lines for a constraint
        PossibleLines generate_lines(int length,
                                     const std::vector<int> &block_lengths,
                                     const std::vector<int> &block_colors,
                                     int max_count = -1);

        // Count possible lines without generating them
        int count_lines(int length,
                        const std::vector<int> &block_lengths,
                        const std::vector<int> &block_colors);

        // Generate lines with additional constraints from color_possible
        PossibleLines generate_lines_with_info(int length,
                                               const std::vector<int> &block_lengths,
                                               const std::vector<int> &block_colors,
                                               const std::vector<std::vector<float>> &info);

        // Helper for generate_lines_with_info
        void generate_lines_with_info_recursive(int length,
                                                const std::vector<int> &block_lengths,
                                                const std::vector<int> &block_colors,
                                                int previous_color,
                                                int pos,
                                                LineArray current,
                                                PossibleLines &result,
                                                const std::vector<std::vector<float>> &info);

        // Update color_possible from generated lines
        void update_color_possible(int orientation, int line_idx,
                                   const PossibleLines &possible_lines);

        // Filter lines based on current color_possible constraints
        PossibleLines filter_lines(int orientation, int line_idx,
                                   const PossibleLines &lines);

        // Extract solution from color_possible
        std::vector<int> extract_solution() const;

        // Check if puzzle is solved
        bool is_solved() const;

        // Member variables
        int width_;
        int height_;
        int n_colors_;
        int limit_generate_;
        bool verbose_;

        std::vector<LineConstraints> h_constraints_; // Horizontal (rows)
        std::vector<LineConstraints> v_constraints_; // Vertical (columns)

        std::vector<LineState> h_states_;
        std::vector<LineState> v_states_;

        ColorPossible color_possible_; // [y][x][color]
    };

} // namespace nonogram
