#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <pybind11/numpy.h>
#include "nonogram_solver.h"

namespace py = pybind11;
using namespace nonogram;

// Wrapper to convert Python input to C++ and back
class NonogramSolverPython
{
public:
    NonogramSolverPython(int width, int height, int n_colors,
                         py::list h_constraints, py::list v_constraints)
    {
        // Convert Python constraints to C++
        std::vector<LineConstraints> h_cons, v_cons;

        for (auto item : h_constraints)
        {
            auto constraint = item.cast<py::dict>();
            LineConstraints lc;
            lc.block_lengths = constraint["block_lengths"].cast<std::vector<int>>();
            lc.block_colors = constraint["block_colors"].cast<std::vector<int>>();
            h_cons.push_back(lc);
        }

        for (auto item : v_constraints)
        {
            auto constraint = item.cast<py::dict>();
            LineConstraints lc;
            lc.block_lengths = constraint["block_lengths"].cast<std::vector<int>>();
            lc.block_colors = constraint["block_colors"].cast<std::vector<int>>();
            v_cons.push_back(lc);
        }

        solver_ = std::make_unique<NonogramSolver>(width, height, n_colors,
                                                   h_cons, v_cons);
    }

    void initialize(int limit_generate)
    {
        solver_->initialize(limit_generate);
    }

    py::array_t<int> solve(bool verbose = false)
    {
        auto result = solver_->solve(verbose);

        // Convert to numpy array
        std::vector<size_t> shape = {static_cast<size_t>(solver_->get_height()), static_cast<size_t>(solver_->get_width())};
        auto arr = py::array_t<int>(shape);
        auto buf = arr.request();
        int *ptr = static_cast<int *>(buf.ptr);

        std::copy(result.begin(), result.end(), ptr);
        return arr;
    }

    py::array_t<int> get_current_state()
    {
        auto result = solver_->get_current_state();

        std::vector<size_t> shape = {static_cast<size_t>(solver_->get_height()), static_cast<size_t>(solver_->get_width())};
        auto arr = py::array_t<int>(shape);
        auto buf = arr.request();
        int *ptr = static_cast<int *>(buf.ptr);

        std::copy(result.begin(), result.end(), ptr);
        return arr;
    }

private:
    std::unique_ptr<NonogramSolver> solver_;
};

PYBIND11_MODULE(nonogram_cpp, m)
{
    m.doc() = "C++ accelerated nonogram solver";

    py::class_<NonogramSolverPython>(m, "NonogramSolver")
        .def(py::init<int, int, int, py::list, py::list>(),
             py::arg("width"),
             py::arg("height"),
             py::arg("n_colors"),
             py::arg("h_constraints"),
             py::arg("v_constraints"))
        .def("initialize", &NonogramSolverPython::initialize,
             py::arg("limit_generate") = 5000000)
        .def("solve", &NonogramSolverPython::solve,
             py::arg("verbose") = false)
        .def("get_current_state", &NonogramSolverPython::get_current_state);
}
