using Calculator.Models;
using Calculator.Services;
using FluentAssertions;
using Xunit;

namespace Calculator.Tests
{
    /// <summary>
    /// Comprehensive unit tests for CalculatorService
    /// </summary>
    public class CalculatorServiceTests
    {
        private readonly ICalculatorService _calculator;

        public CalculatorServiceTests()
        {
            _calculator = new CalculatorService();
        }

        [Theory]
        [InlineData(5, 3, 8)]
        [InlineData(-2, 7, 5)]
        [InlineData(0, 0, 0)]
        [InlineData(double.MaxValue, 1, double.MaxValue)]
        public async Task AddAsync_ValidInputs_ReturnsCorrectResult(double a, double b, double expected)
        {
            // Act
            var result = await _calculator.AddAsync(a, b);
            
            // Assert
            result.Should().NotBeNull();
            result.IsValid.Should().BeTrue();
            result.Value.Should().Be(expected);
            result.Operation.Should().Be($"{a} + {b}");
            result.Timestamp.Should().BeCloseTo(DateTime.UtcNow, TimeSpan.FromSeconds(1));
        }

        [Theory]
        [InlineData(10, 3, 7)]
        [InlineData(0, 5, -5)]
        [InlineData(-8, -2, -6)]
        public async Task SubtractAsync_ValidInputs_ReturnsCorrectResult(double a, double b, double expected)
        {
            // Act
            var result = await _calculator.SubtractAsync(a, b);
            
            // Assert
            result.IsValid.Should().BeTrue();
            result.Value.Should().Be(expected);
            result.Operation.Should().Contain("–").Or.Contain("-");
        }

        [Theory]
        [InlineData(4, 5, 20)]
        [InlineData(-3, 4, -12)]
        [InlineData(0, 100, 0)]
        [InlineData(2.5, 4, 10)]
        public async Task MultiplyAsync_ValidInputs_ReturnsCorrectResult(double a, double b, double expected)
        {
            // Act
            var result = await _calculator.MultiplyAsync(a, b);
            
            // Assert
            result.IsValid.Should().BeTrue();
            result.Value.Should().BeApproximately(expected, 0.001);
        }

        [Theory]
        [InlineData(10, 2, 5)]
        [InlineData(7, 2, 3.5)]
        [InlineData(-8, 4, -2)]
        public async Task DivideAsync_ValidInputs_ReturnsCorrectResult(double a, double b, double expected)
        {
            // Act
            var result = await _calculator.DivideAsync(a, b);
            
            // Assert
            result.IsValid.Should().BeTrue();
            result.Value.Should().BeApproximately(expected, 0.001);
        }

        [Theory]
        [InlineData(10, 0)]
        [InlineData(-5, 0)]
        [InlineData(0, 0)]
        public async Task DivideAsync_DivisionByZero_ReturnsError(double a, double b)
        {
            // Act
            var result = await _calculator.DivideAsync(a, b);
            
            // Assert
            result.IsValid.Should().BeFalse();
            result.ErrorMessage.Should().Contain("Division by zero");
            result.Value.Should().Be(0);
        }

        [Theory]
        [InlineData(2, 3, 8)]
        [InlineData(5, 2, 25)]
        [InlineData(10, 0, 1)]
        [InlineData(4, 0.5, 2)]
        public async Task PowerAsync_ValidInputs_ReturnsCorrectResult(double baseValue, double exponent, double expected)
        {
            // Act
            var result = await _calculator.PowerAsync(baseValue, exponent);
            
            // Assert
            result.IsValid.Should().BeTrue();
            result.Value.Should().BeApproximately(expected, 0.001);
        }

        [Fact]
        public async Task PowerAsync_ZeroToNegativePower_ReturnsError()
        {
            // Act
            var result = await _calculator.PowerAsync(0, -1);
            
            // Assert
            result.IsValid.Should().BeFalse();
            result.ErrorMessage.Should().Contain("Cannot raise zero to a negative power");
        }

        [Theory]
        [InlineData(16, 4)]
        [InlineData(25, 5)]
        [InlineData(0, 0)]
        [InlineData(2, 1.414)]
        public async Task SquareRootAsync_ValidInputs_ReturnsCorrectResult(double value, double expected)
        {
            // Act
            var result = await _calculator.SquareRootAsync(value);
            
            // Assert
            result.IsValid.Should().BeTrue();
            result.Value.Should().BeApproximately(expected, 0.001);
        }

        [Theory]
        [InlineData(-1)]
        [InlineData(-100)]
        public async Task SquareRootAsync_NegativeInput_ReturnsError(double value)
        {
            // Act
            var result = await _calculator.SquareRootAsync(value);
            
            // Assert
            result.IsValid.Should().BeFalse();
            result.ErrorMessage.Should().Contain("Cannot calculate square root of negative number");
        }

        [Fact]
        public async Task GetHistoryAsync_AfterOperations_ReturnsCorrectHistory()
        {
            // Arrange
            await _calculator.ClearHistoryAsync();
            await _calculator.AddAsync(1, 2);
            await _calculator.MultiplyAsync(3, 4);
            await _calculator.DivideAsync(10, 0); // This should create an error
            
            // Act
            var history = await _calculator.GetHistoryAsync();
            
            // Assert
            history.Should().HaveCount(3);
            history.Count(h => h.IsValid).Should().Be(2);
            history.Count(h => !h.IsValid).Should().Be(1);
        }

        [Fact]
        public async Task ClearHistoryAsync_RemovesAllHistory()
        {
            // Arrange
            await _calculator.AddAsync(1, 1);
            await _calculator.SubtractAsync(5, 2);
            
            // Act
            await _calculator.ClearHistoryAsync();
            var history = await _calculator.GetHistoryAsync();
            
            // Assert
            history.Should().BeEmpty();
        }

        [Fact]
        public async Task ConcurrentOperations_ShouldBeThreadSafe()
        {
            // Arrange
            await _calculator.ClearHistoryAsync();
            
            // Act - Run multiple operations concurrently
            var tasks = Enumerable.Range(1, 10)
                .Select(i => _calculator.AddAsync(i, i))
                .ToList();
            
            var results = await Task.WhenAll(tasks);
            var history = await _calculator.GetHistoryAsync();
            
            // Assert
            results.Should().HaveCount(10);
            results.Should().OnlyContain(r => r.IsValid);
            history.Should().HaveCount(10);
            
            // Verify all operations completed correctly
            var expectedSum = Enumerable.Range(1, 10).Sum(i => i + i);
            var actualSum = results.Sum(r => r.Value);
            actualSum.Should().Be(expectedSum);
        }
    }
}