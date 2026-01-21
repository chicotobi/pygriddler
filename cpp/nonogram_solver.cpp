#include "nonogram_solver.h"
#include <algorithm>
#include <iostream>
#include <set>

namespace nonogram
{

    NonogramSolver::NonogramSolver(int width, int height, int n_colors,
                                   const std::vector<LineConstraints> &h_constraints,
                                   const std::vector<LineConstraints> &v_constraints)
        : width_(width), height_(height), n_colors_(n_colors),
          h_constraints_(h_constraints), v_constraints_(v_constraints),
          limit_generate_(5000000), verbose_(false)
    {

        // Initialize color_possible to all 1.0 (all colors possible everywhere)
        color_possible_.resize(height_);
        for (int y = 0; y < height_; ++y)
        {
            color_possible_[y].resize(width_);
            for (int x = 0; x < width_; ++x)
            {
                color_possible_[y][x].resize(n_colors_, 1.0f);
            }
        }

        // Initialize line states
        h_states_.resize(height_);
        v_states_.resize(width_);
    }

    std::vector<std::vector<float>> NonogramSolver::generate_initial_color_possible(
        int length,
        const std::vector<int> &block_lengths,
        const std::vector<int> &block_colors)
    {
        std::vector<std::vector<float>> color_possible(length, std::vector<float>(n_colors_, 0.0f));
        
        // Zero (white) is always possible
        for (int i = 0; i < length; ++i)
        {
            color_possible[i][0] = 1.0f;
        }
        
        // Edge case: if no blocks, only white is possible
        if (block_lengths.empty())
        {
            return color_possible;
        }
        
        // Create compressed representation of the line
        std::vector<int> line;
        for (size_t i = 0; i < block_lengths.size(); ++i)
        {
            if (i > 0 && block_colors[i] == block_colors[i-1])
            {
                line.push_back(0); // Mandatory white space between same-colored blocks
            }
            for (int j = 0; j < block_lengths[i]; ++j)
            {
                line.push_back(block_colors[i]);
            }
        }
        
        // For each possible starting position
        for (int i = 0; i <= length - (int)line.size(); ++i)
        {
            for (size_t j = 0; j < line.size(); ++j)
            {
                int c = line[j];
                color_possible[i + j][c] = 1.0f;
            }
        }
        
        return color_possible;
    }

    void NonogramSolver::initialize(int limit_generate)
    {
        limit_generate_ = limit_generate;

        // Initial color_possible sweep (like Python's generate_color_possible)
        // This creates simple constraints even for lines that are only counted
        for (int y = 0; y < height_; ++y)
        {
            std::vector<std::vector<float>> line_color_possible = 
                generate_initial_color_possible(width_, h_constraints_[y].block_lengths,
                                                h_constraints_[y].block_colors);
            // AND with existing color_possible
            for (int x = 0; x < width_; ++x)
            {
                for (int c = 0; c < n_colors_; ++c)
                {
                    color_possible_[y][x][c] = color_possible_[y][x][c] * line_color_possible[x][c];
                }
            }
        }

        // Transpose and process vertical
        for (int x = 0; x < width_; ++x)
        {
            std::vector<std::vector<float>> line_color_possible = 
                generate_initial_color_possible(height_, v_constraints_[x].block_lengths,
                                                v_constraints_[x].block_colors);
            // AND with existing color_possible
            for (int y = 0; y < height_; ++y)
            {
                for (int c = 0; c < n_colors_; ++c)
                {
                    color_possible_[y][x][c] = color_possible_[y][x][c] * line_color_possible[y][c];
                }
            }
        }

        // Generate or count possible lines for each constraint
        for (int y = 0; y < height_; ++y)
        {
            int count = count_lines(width_, h_constraints_[y].block_lengths,
                                    h_constraints_[y].block_colors);

            if (count < limit_generate_)
            {
                h_states_[y].possible_lines = generate_lines(width_,
                                                             h_constraints_[y].block_lengths,
                                                             h_constraints_[y].block_colors);
                h_states_[y].generated = true;
                h_states_[y].count = count;
                
                if (verbose_)
                    printf("O0L%03d Generated  %9d\n", y, count);
            }
            else
            {
                h_states_[y].generated = false;
                h_states_[y].count = count;
                
                if (verbose_)
                    printf("O0L%03d Counted    %9d\n", y, count);
            }
        }

        for (int x = 0; x < width_; ++x)
        {
            int count = count_lines(height_, v_constraints_[x].block_lengths,
                                    v_constraints_[x].block_colors);

            if (count < limit_generate_)
            {
                v_states_[x].possible_lines = generate_lines(height_,
                                                             v_constraints_[x].block_lengths,
                                                             v_constraints_[x].block_colors);
                v_states_[x].generated = true;
                v_states_[x].count = count;
                
                if (verbose_)
                    printf("O1L%03d Generated  %9d\n", x, count);
            }
            else
            {
                v_states_[x].generated = false;
                v_states_[x].count = count;
                
                if (verbose_)
                    printf("O1L%03d Counted    %9d\n", x, count);
            }
        }
    }

    std::vector<int> NonogramSolver::solve(bool verbose)
    {
        verbose_ = verbose;

        int iteration = 0;
        const int max_iterations = 1000;
        
        while (!is_solved() && iteration < max_iterations)
        {
            iteration++;
            if (verbose_)
            {
                std::cout << "\nIteration " << iteration << std::endl;
            }

            if (!solve_iteration())
            {
                // Need to generate new lines
                if (verbose_)
                {
                    std::cout << "\nNo update to color_possible: Generate new solutions" << std::endl;
                }

                bool generated_any = false;

                // Try to generate lines for ungenerated constraints
                for (int y = 0; y < height_; ++y)
                {
                    if (h_states_[y].generated)
                        continue;

                    // Extract color_possible info for this line
                    std::vector<std::vector<float>> info(width_);
                    for (int x = 0; x < width_; ++x)
                    {
                        
                        if (verbose_)
                            printf("O0L%03d Generated  %9d\n", y, h_states_[y].count);
                    }
                }

                for (int x = 0; x < width_; ++x)
                {
                    if (v_states_[x].generated)
                        continue;

                    std::vector<std::vector<float>> info(height_);
                    for (int y = 0; y < height_; ++y)
                    {
                        info[y] = color_possible_[y][x];
                    }

                    int count = v_states_[x].count;
                    if (count < limit_generate_)
                    {
                        v_states_[x].possible_lines = generate_lines_with_info(
                            height_, v_constraints_[x].block_lengths,
                            v_constraints_[x].block_colors, info);
                        v_states_[x].generated = true;
                        v_states_[x].count = v_states_[x].possible_lines.size();
                        generated_any = true;
                        
                        if (verbose_)
                            printf("O1L%03d Generated  %9d\n", x, v_states_[x].count);
                    }
                }

                if (!generated_any)
                {
                    // Force generate the smallest ungenerated line
                    if (verbose_)
                    {
                        std::cout << "Forcing generation of smallest line" << std::endl;
                    }

                    int min_count = limit_generate_ * 10;
                    int best_ori = -1;
                    int best_idx = -1;

                    for (int y = 0; y < height_; ++y)
                    {
                        if (!h_states_[y].generated && h_states_[y].count < min_count)
                        {
                            min_count = h_states_[y].count;
                            best_ori = 0;
                            best_idx = y;
                        }
                    }

                    for (int x = 0; x < width_; ++x)
                    {
                        if (!v_states_[x].generated && v_states_[x].count < min_count)
                        {
                            min_count = v_states_[x].count;
                            best_ori = 1;
                            best_idx = x;
                        }
                    }

                    if (best_ori == 0)
                    {
                        std::vector<std::vector<float>> info(width_);
                        for (int x = 0; x < width_; ++x)
                        {
                            info[x] = color_possible_[best_idx][x];
                        }
                        h_states_[best_idx].possible_lines = generate_lines_with_info(
                            width_, h_constraints_[best_idx].block_lengths,
                            h_constraints_[best_idx].block_colors, info);
                        h_states_[best_idx].generated = true;
                        h_states_[best_idx].count = h_states_[best_idx].possible_lines.size();
                    }
                    else if (best_ori == 1)
                    {
                        std::vector<std::vector<float>> info(height_);
                        for (int y = 0; y < height_; ++y)
                        {
                            info[y] = color_possible_[y][best_idx];
                        }
                        v_states_[best_idx].possible_lines = generate_lines_with_info(
                            height_, v_constraints_[best_idx].block_lengths,
                            v_constraints_[best_idx].block_colors, info);
                        v_states_[best_idx].generated = true;
                        v_states_[best_idx].count = v_states_[best_idx].possible_lines.size();
                    }
                }
            }
        }

        if (iteration >= max_iterations && !is_solved())
        {
            std::cout << "\nWarning: Reached maximum iterations (" << max_iterations << ") without solving puzzle" << std::endl;
        }

        return extract_solution();
    }

    bool NonogramSolver::solve_iteration()
    {
        ColorPossible old_color_possible = color_possible_;

        // Process horizontal lines
        for (int y = 0; y < height_; ++y)
        {
            if (!h_states_[y].generated)
                continue;

            int old_count = h_states_[y].count;
            
            // Filter lines based on current constraints
            PossibleLines filtered = filter_lines(0, y, h_states_[y].possible_lines);
            h_states_[y].possible_lines = filtered;
            h_states_[y].count = filtered.size();

            // Output status like Python solver
            if (verbose_)
            {
                std::string status;
                if (h_states_[y].count == 1)
                    status = "Finished  ";
                else if (h_states_[y].count == old_count)
                    status = "Same at   ";
                else
                    status = "Reduced to";
                
                printf("O0L%03d %s %9d", y, status.c_str(), h_states_[y].count);
                if (h_states_[y].count != old_count && h_states_[y].count > 1)
                    printf(" from %9d", old_count);
                printf("\n");
                fflush(stdout);
            }

            // Update color_possible based on remaining lines
            update_color_possible(0, y, filtered);
        }

        // Process vertical lines
        for (int x = 0; x < width_; ++x)
        {
            if (!v_states_[x].generated)
                continue;

            int old_count = v_states_[x].count;
            
            // Filter lines based on current constraints
            PossibleLines filtered = filter_lines(1, x, v_states_[x].possible_lines);
            v_states_[x].possible_lines = filtered;
            v_states_[x].count = filtered.size();

            // Output status like Python solver
            if (verbose_)
            {
                std::string status;
                if (v_states_[x].count == 1)
                    status = "Finished  ";
                else if (v_states_[x].count == old_count)
                    status = "Same at   ";
                else
                    status = "Reduced to";
                
                printf("O1L%03d %s %9d", x, status.c_str(), v_states_[x].count);
                if (v_states_[x].count != old_count && v_states_[x].count > 1)
                    printf(" from %9d", old_count);
                printf("\n");
                fflush(stdout);
            }

            // Update color_possible based on remaining lines
            update_color_possible(1, x, filtered);
        }

        // Check if any progress was made
        for (int y = 0; y < height_; ++y)
        {
            for (int x = 0; x < width_; ++x)
            {
                for (int c = 0; c < n_colors_; ++c)
                {
                    if (old_color_possible[y][x][c] != color_possible_[y][x][c])
                    {
                        return true; // Progress made
                    }
                }
            }
        }

        return false; // No progress
    }

    PossibleLines NonogramSolver::filter_lines(int orientation, int line_idx,
                                               const PossibleLines &lines)
    {
        PossibleLines filtered;

        for (const auto &line : lines)
        {
            bool valid = true;

            // Check if line is compatible with color_possible
            for (size_t pos = 0; pos < line.size(); ++pos)
            {
                int color = line[pos];

                float allowed;
                if (orientation == 0)
                { // Horizontal
                    allowed = color_possible_[line_idx][pos][color];
                }
                else
                { // Vertical
                    allowed = color_possible_[pos][line_idx][color];
                }

                if (allowed < 0.5f)
                {
                    valid = false;
                    break;
                }
            }

            if (valid)
            {
                filtered.push_back(line);
            }
        }

        return filtered;
    }

    void NonogramSolver::update_color_possible(int orientation, int line_idx,
                                               const PossibleLines &possible_lines)
    {
        if (possible_lines.empty())
            return;

        int length = possible_lines[0].size();

        // For each position, collect which colors appear
        for (int pos = 0; pos < length; ++pos)
        {
            std::vector<bool> colors_present(n_colors_, false);

            for (const auto &line : possible_lines)
            {
                colors_present[line[pos]] = true;
            }

            // Update color_possible to reflect only colors that appear
            for (int c = 0; c < n_colors_; ++c)
            {
                if (!colors_present[c])
                {
                    if (orientation == 0)
                    { // Horizontal
                        color_possible_[line_idx][pos][c] = 0.0f;
                    }
                    else
                    { // Vertical
                        color_possible_[pos][line_idx][c] = 0.0f;
                    }
                }
            }
        }
    }

    PossibleLines NonogramSolver::generate_lines(int length,
                                                 const std::vector<int> &block_lengths,
                                                 const std::vector<int> &block_colors,
                                                 int max_count)
    {
        PossibleLines lines;
        generate_lines_recursive(length, block_lengths, block_colors, -1, 0, LineArray(length, 0), lines);
        return lines;
    }

    void NonogramSolver::generate_lines_recursive(int length,
                                                                                               const std::vector<int> &block_lengths,
                                                                                               const std::vector<int> &block_colors,
                                                                                               int previous_color,
                                                                                               int pos,
                                                                                               LineArray current,
                                                                                               PossibleLines &result)
                                                 {
                                                     // Base case: all blocks placed
                                                     if (block_lengths.empty())
                                                     {
                                                         result.push_back(current);
                                                         return;
                                                     }

                                                     // Calculate minimum space needed for remaining blocks
                                                     int min_space = 0;
                                                     for (size_t i = 0; i < block_lengths.size(); ++i)
                                                     {
                                                         min_space += block_lengths[i];
                                                     }
                                                     // Add gaps between same-colored adjacent blocks
                                                     for (size_t i = 1; i < block_colors.size(); ++i)
                                                     {
                                                         if (block_colors[i] == block_colors[i - 1])
                                                         {
                                                             min_space++;
                                                         }
                                                     }

                                                     int max_white_space = length - pos - min_space;
                                                     int start_white = (block_colors[0] == previous_color) ? 1 : 0;

                                                     // Try different amounts of white space before next block
                                                     for (int white = start_white; white <= max_white_space; ++white)
                                                     {
                                                         // Place white spaces
                                                         int block_start = pos + white;
                                                         int block_end = block_start + block_lengths[0];

                                                         // Place the colored block
                                                         LineArray next = current;
                                                         for (int i = block_start; i < block_end; ++i)
                                                         {
                                                             next[i] = block_colors[0];
                                                         }

                                                         // Recurse with remaining blocks
                                                         std::vector<int> remaining_lengths(block_lengths.begin() + 1, block_lengths.end());
                                                         std::vector<int> remaining_colors(block_colors.begin() + 1, block_colors.end());

                                                         generate_lines_recursive(length, remaining_lengths, remaining_colors,
                                                                                  block_colors[0], block_end, next, result);
                                                     }
                                                 }

                                                 int NonogramSolver::count_lines(int length,
                                                                                 const std::vector<int> &block_lengths,
                                                                                 const std::vector<int> &block_colors)
                                                 {
                                                     return count_lines_recursive(length, block_lengths, block_colors, -1);
                                                 }

                                                 int NonogramSolver::count_lines_recursive(int length,
                                                                                           const std::vector<int> &block_lengths,
                                                                                           const std::vector<int> &block_colors,
                                                                                           int previous_color)
                                                 {
                                                     if (block_lengths.empty())
                                                     {
                                                         return 1;
                                                     }

                                                     int min_space = 0;
                                                     for (size_t i = 0; i < block_lengths.size(); ++i)
                                                     {
                                                         min_space += block_lengths[i];
                                                     }
                                                     for (size_t i = 1; i < block_colors.size(); ++i)
                                                     {
                                                         if (block_colors[i] == block_colors[i - 1])
                                                         {
                                                             min_space++;
                                                         }
                                                     }

                                                     int max_white_space = length - min_space;
                                                     int start_white = (block_lengths.size() > 0 && block_colors[0] == previous_color) ? 1 : 0;

                                                     int total = 0;
                                                     for (int white = start_white; white <= max_white_space; ++white)
                                                     {
                                                         std::vector<int> remaining_lengths(block_lengths.begin() + 1, block_lengths.end());
                                                         std::vector<int> remaining_colors(block_colors.begin() + 1, block_colors.end());

                                                         int remaining_length = length - white - block_lengths[0];
                                                         total += count_lines_recursive(remaining_length, remaining_lengths,
                                                                                        remaining_colors, block_colors[0]);
                                                     }

                                                     return total;
                                                 }

                                                 PossibleLines NonogramSolver::generate_lines_with_info(
                                                     int length,
                                                     const std::vector<int> &block_lengths,
                                                     const std::vector<int> &block_colors,
                                                     const std::vector<std::vector<float>> &info)
                                                 {
                                                     PossibleLines lines;
                                                     generate_lines_with_info_recursive(length, block_lengths, block_colors, -1, 0,
                                                                                        LineArray(length, 0), lines, info);
                                                     return lines;
                                                 }

                                                 void NonogramSolver::generate_lines_with_info_recursive(
                                                     int length,
                                                     const std::vector<int> &block_lengths,
                                                     const std::vector<int> &block_colors,
                                                     int previous_color,
                                                     int pos,
                                                     LineArray current,
                                                     PossibleLines &result,
                                                     const std::vector<std::vector<float>> &info)
                                                 {
                                                     // Base case: all blocks placed
                                                     if (block_lengths.empty())
                                                     {
                                                         // Check if remaining positions allow white (color 0)
                                                         bool valid = true;
                                                         for (int i = pos; i < length; ++i)
                                                         {
                                                             if (info[i][0] < 0.5f)
                                                             {
                                                                 valid = false;
                                                                 break;
                                                             }
                                                         }
                                                         if (valid)
                                                         {
                                                             result.push_back(current);
                                                         }
                                                         return;
                                                     }

                                                     // Calculate minimum space needed
                                                     int min_space = 0;
                                                     for (size_t i = 0; i < block_lengths.size(); ++i)
                                                     {
                                                         min_space += block_lengths[i];
                                                     }
                                                     for (size_t i = 1; i < block_colors.size(); ++i)
                                                     {
                                                         if (block_colors[i] == block_colors[i - 1])
                                                         {
                                                             min_space++;
                                                         }
                                                     }

                                                     // Find max white space considering constraints
                                                     int max_white_space_input = length - pos - min_space;

                                                     // Find first position where white is not allowed
                                                     int max_white_space_info = length - pos;
                                                     for (int i = pos; i < length; ++i)
                                                     {
                                                         if (info[i][0] < 0.5f)
                                                         {
                                                             max_white_space_info = i - pos;
                                                             break;
                                                         }
                                                     }

                                                     int max_white_space = std::min(max_white_space_input, max_white_space_info);
                                                     int start_white = (block_colors[0] == previous_color) ? 1 : 0;

                                                     // Try different amounts of white space
                                                     for (int white = start_white; white <= max_white_space; ++white)
                                                     {
                                                         int block_start = pos + white;
                                                         int block_end = block_start + block_lengths[0];

                                                         // Check if block can be placed (all positions allow this color)
                                                         bool block_valid = true;
                                                         for (int i = block_start; i < block_end; ++i)
                                                         {
                                                             if (info[i][block_colors[0]] < 0.5f)
                                                             {
                                                                 block_valid = false;
                                                                 break;
                                                             }
                                                         }

                                                         if (!block_valid)
                                                             continue;

                                                         // Place the block
                                                         LineArray next = current;
                                                         for (int i = block_start; i < block_end; ++i)
                                                         {
                                                             next[i] = block_colors[0];
                                                         }

                                                         // Recurse
                                                         std::vector<int> remaining_lengths(block_lengths.begin() + 1, block_lengths.end());
                                                         std::vector<int> remaining_colors(block_colors.begin() + 1, block_colors.end());

                                                         generate_lines_with_info_recursive(length, remaining_lengths, remaining_colors,
                                                                                            block_colors[0], block_end, next, result, info);
                                                     }
                                                 }

    std::vector<int> NonogramSolver::extract_solution() const
    {
        std::vector<int> solution(width_ * height_);

        for (int y = 0; y < height_; ++y)
        {
            for (int x = 0; x < width_; ++x)
            {
                int solved_color = -1;
                int count_possible = 0;

                for (int c = 0; c < n_colors_; ++c)
                {
                    if (color_possible_[y][x][c] > 0.5f)
                    {
                        solved_color = c;
                        count_possible++;
                    }
                }

                solution[y * width_ + x] = (count_possible == 1) ? solved_color : -1;
            }
        }

        return solution;
    }

    std::vector<int> NonogramSolver::get_current_state() const
    {
        return extract_solution();
    }

    bool NonogramSolver::is_solved() const
    {
        // Check if all cells have exactly one possible color
        for (int y = 0; y < height_; ++y)
        {
            for (int x = 0; x < width_; ++x)
            {
                int count = 0;
                for (int c = 0; c < n_colors_; ++c)
                {
                    if (color_possible_[y][x][c] > 0.5f)
                    {
                        count++;
                    }
                }
                if (count != 1)
                {
                    return false;
                }
            }
        }
        return true;
    }

} // namespace nonogram
