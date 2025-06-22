using Calculator.Models;

namespace Calculator.Services
{
    /// <summary>
    /// Advanced calculator service with async operations and history tracking
    /// </summary>
    public class CalculatorService : ICalculatorService
    {
        private readonly List<CalculationResult> _history;
        private readonly SemaphoreSlim _semaphore;

        public CalculatorService()
        {
            _history = new List<CalculationResult>();
            _semaphore = new SemaphoreSlim(1, 1);
        }

        public async Task<CalculationResult> AddAsync(double a, double b)
        {
            await _semaphore.WaitAsync();
            try
            {
                await Task.Delay(10); // Simulate some async work
                var result = new CalculationResult(a + b, $"{a} + {b}");
                _history.Add(result);
                return result;
            }
            finally
            {
                _semaphore.Release();
            }
        }

        public async Task<CalculationResult> SubtractAsync(double a, double b)
        {
            await _semaphore.WaitAsync();
            try
            {
                await Task.Delay(10);
                var result = new CalculationResult(a - b, $"{a} - {b}");
                _history.Add(result);
                return result;
            }
            finally
            {
                _semaphore.Release();
            }
        }

        public async Task<CalculationResult> MultiplyAsync(double a, double b)
        {
            await _semaphore.WaitAsync();
            try
            {
                await Task.Delay(15); // Slightly longer for multiplication
                var result = new CalculationResult(a * b, $"{a} * {b}");
                _history.Add(result);
                return result;
            }
            finally
            {
                _semaphore.Release();
            }
        }

        public async Task<CalculationResult> DivideAsync(double a, double b)
        {
            await _semaphore.WaitAsync();
            try
            {
                await Task.Delay(20); // Even longer for division
                
                if (Math.Abs(b) < double.Epsilon)
                {
                    var errorResult = CalculationResult.Error("Division by zero is not allowed");
                    _history.Add(errorResult);
                    return errorResult;
                }

                var result = new CalculationResult(a / b, $"{a} / {b}");
                _history.Add(result);
                return result;
            }
            finally
            {
                _semaphore.Release();
            }
        }

        public async Task<CalculationResult> PowerAsync(double baseValue, double exponent)
        {
            await _semaphore.WaitAsync();
            try
            {
                await Task.Delay(25); // Complex operation takes longer
                
                if (baseValue == 0 && exponent < 0)
                {
                    var errorResult = CalculationResult.Error("Cannot raise zero to a negative power");
                    _history.Add(errorResult);
                    return errorResult;
                }

                var value = Math.Pow(baseValue, exponent);
                var result = new CalculationResult(value, $"{baseValue} ^ {exponent}");
                _history.Add(result);
                return result;
            }
            finally
            {
                _semaphore.Release();
            }
        }

        public async Task<CalculationResult> SquareRootAsync(double value)
        {
            await _semaphore.WaitAsync();
            try
            {
                await Task.Delay(15);
                
                if (value < 0)
                {
                    var errorResult = CalculationResult.Error("Cannot calculate square root of negative number");
                    _history.Add(errorResult);
                    return errorResult;
                }

                var result = new CalculationResult(Math.Sqrt(value), $"√{value}");
                _history.Add(result);
                return result;
            }
            finally
            {
                _semaphore.Release();
            }
        }

        public async Task<List<CalculationResult>> GetHistoryAsync()
        {
            await _semaphore.WaitAsync();
            try
            {
                await Task.Delay(5);
                return new List<CalculationResult>(_history);
            }
            finally
            {
                _semaphore.Release();
            }
        }

        public async Task ClearHistoryAsync()
        {
            await _semaphore.WaitAsync();
            try
            {
                await Task.Delay(5);
                _history.Clear();
            }
            finally
            {
                _semaphore.Release();
            }
        }
    }
}