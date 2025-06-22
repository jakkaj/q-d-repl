using Calculator.Models;

namespace Calculator.Services
{
    /// <summary>
    /// Interface for calculator operations
    /// </summary>
    public interface ICalculatorService
    {
        Task<CalculationResult> AddAsync(double a, double b);
        Task<CalculationResult> SubtractAsync(double a, double b);
        Task<CalculationResult> MultiplyAsync(double a, double b);
        Task<CalculationResult> DivideAsync(double a, double b);
        Task<CalculationResult> PowerAsync(double baseValue, double exponent);
        Task<CalculationResult> SquareRootAsync(double value);
        Task<List<CalculationResult>> GetHistoryAsync();
        Task ClearHistoryAsync();
    }
}