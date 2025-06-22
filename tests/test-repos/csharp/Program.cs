using Calculator.Models;
using Calculator.Services;
using Newtonsoft.Json;

namespace Calculator
{
    /// <summary>
    /// Console application demonstrating async calculator operations
    /// </summary>
    class Program
    {
        private static ICalculatorService _calculator = new CalculatorService();

        static async Task Main(string[] args)
        {
            Console.WriteLine("=== Advanced Async Calculator ===");
            
            try
            {
                // Demonstrate basic operations
                await DemoBasicOperations();
                
                // Demonstrate error handling
                await DemoErrorHandling();
                
                // Demonstrate concurrent operations
                await DemoConcurrentOperations();
                
                // Show history
                await ShowCalculationHistory();
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Application error: {ex.Message}");
            }
            
            Console.WriteLine("Press any key to exit...");
            Console.ReadKey();
        }

        private static async Task DemoBasicOperations()
        {
            Console.WriteLine("\n--- Basic Operations ---");
            
            var add = await _calculator.AddAsync(10, 5);
            Console.WriteLine($"Addition: {add}");
            
            var subtract = await _calculator.SubtractAsync(10, 3);
            Console.WriteLine($"Subtraction: {subtract}");
            
            var multiply = await _calculator.MultiplyAsync(4, 7);
            Console.WriteLine($"Multiplication: {multiply}");
            
            var divide = await _calculator.DivideAsync(20, 4);
            Console.WriteLine($"Division: {divide}");
            
            var power = await _calculator.PowerAsync(2, 8);
            Console.WriteLine($"Power: {power}");
            
            var sqrt = await _calculator.SquareRootAsync(16);
            Console.WriteLine($"Square Root: {sqrt}");
        }

        private static async Task DemoErrorHandling()
        {
            Console.WriteLine("\n--- Error Handling ---");
            
            var divideByZero = await _calculator.DivideAsync(10, 0);
            Console.WriteLine($"Divide by zero: {divideByZero}");
            
            var negativeRoot = await _calculator.SquareRootAsync(-4);
            Console.WriteLine($"Negative square root: {negativeRoot}");
            
            var invalidPower = await _calculator.PowerAsync(0, -1);
            Console.WriteLine($"Invalid power: {invalidPower}");
        }

        private static async Task DemoConcurrentOperations()
        {
            Console.WriteLine("\n--- Concurrent Operations ---");
            
            var tasks = new List<Task<CalculationResult>>
            {
                _calculator.AddAsync(1, 1),
                _calculator.MultiplyAsync(2, 2),
                _calculator.PowerAsync(3, 2),
                _calculator.SquareRootAsync(25),
                _calculator.DivideAsync(100, 10)
            };
            
            var results = await Task.WhenAll(tasks);
            
            Console.WriteLine("Concurrent calculation results:");
            foreach (var result in results)
            {
                Console.WriteLine($"  {result}");
            }
        }

        private static async Task ShowCalculationHistory()
        {
            Console.WriteLine("\n--- Calculation History ---");
            
            var history = await _calculator.GetHistoryAsync();
            Console.WriteLine($"Total calculations performed: {history.Count}");
            
            var validCalculations = history.Where(h => h.IsValid).ToList();
            var errorCalculations = history.Where(h => !h.IsValid).ToList();
            
            Console.WriteLine($"Successful: {validCalculations.Count}, Errors: {errorCalculations.Count}");
            
            if (validCalculations.Any())
            {
                var avgValue = validCalculations.Average(c => c.Value);
                var maxValue = validCalculations.Max(c => c.Value);
                var minValue = validCalculations.Min(c => c.Value);
                
                Console.WriteLine($"Statistics - Avg: {avgValue:F2}, Max: {maxValue:F2}, Min: {minValue:F2}");
            }
            
            // Export history as JSON
            var jsonHistory = JsonConvert.SerializeObject(history, Formatting.Indented);
            Console.WriteLine("\nHistory as JSON:");
            Console.WriteLine(jsonHistory);
        }
    }
}