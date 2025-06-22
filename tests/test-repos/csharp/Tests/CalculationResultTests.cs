using Calculator.Models;
using FluentAssertions;
using Newtonsoft.Json;
using Xunit;

namespace Calculator.Tests
{
    /// <summary>
    /// Unit tests for CalculationResult model
    /// </summary>
    public class CalculationResultTests
    {
        [Fact]
        public void DefaultConstructor_SetsCorrectDefaults()
        {
            // Act
            var result = new CalculationResult();
            
            // Assert
            result.Value.Should().Be(0);
            result.Operation.Should().Be(string.Empty);
            result.IsValid.Should().BeFalse();
            result.ErrorMessage.Should().BeNull();
            result.Timestamp.Should().BeCloseTo(DateTime.UtcNow, TimeSpan.FromSeconds(1));
        }

        [Fact]
        public void ParameterizedConstructor_SetsCorrectValues()
        {
            // Arrange
            var value = 42.5;
            var operation = "test operation";
            
            // Act
            var result = new CalculationResult(value, operation);
            
            // Assert
            result.Value.Should().Be(value);
            result.Operation.Should().Be(operation);
            result.IsValid.Should().BeTrue();
            result.ErrorMessage.Should().BeNull();
            result.Timestamp.Should().BeCloseTo(DateTime.UtcNow, TimeSpan.FromSeconds(1));
        }

        [Fact]
        public void Error_CreatesErrorResult()
        {
            // Arrange
            var errorMessage = "Test error message";
            
            // Act
            var result = CalculationResult.Error(errorMessage);
            
            // Assert
            result.IsValid.Should().BeFalse();
            result.ErrorMessage.Should().Be(errorMessage);
            result.Value.Should().Be(0);
            result.Operation.Should().Be("error");
        }

        [Fact]
        public void ToJson_SerializesCorrectly()
        {
            // Arrange
            var result = new CalculationResult(123.45, "test operation");
            
            // Act
            var json = result.ToJson();
            var deserialized = JsonConvert.DeserializeObject<CalculationResult>(json);
            
            // Assert
            json.Should().NotBeNullOrEmpty();
            deserialized.Should().NotBeNull();
            deserialized!.Value.Should().Be(result.Value);
            deserialized.Operation.Should().Be(result.Operation);
            deserialized.IsValid.Should().Be(result.IsValid);
        }

        [Fact]
        public void ToString_ValidResult_FormatsCorrectly()
        {
            // Arrange
            var result = new CalculationResult(42.123, "2 + 40");
            
            // Act
            var str = result.ToString();
            
            // Assert
            str.Should().Contain("2 + 40");
            str.Should().Contain("42.12");
            str.Should().Contain(result.Timestamp.ToString("yyyy-MM-dd HH:mm:ss"));
        }

        [Fact]
        public void ToString_ErrorResult_FormatsError()
        {
            // Arrange
            var errorMessage = "Division by zero";
            var result = CalculationResult.Error(errorMessage);
            
            // Act
            var str = result.ToString();
            
            // Assert
            str.Should().StartWith("Error:");
            str.Should().Contain(errorMessage);
        }

        [Theory]
        [InlineData(0, "zero")]
        [InlineData(3.14159, "pi")]
        [InlineData(-273.15, "absolute zero")]
        [InlineData(double.MaxValue, "max value")]
        [InlineData(double.MinValue, "min value")]
        public void CalculationResult_VariousValues_HandlesCorrectly(double value, string operation)
        {
            // Act
            var result = new CalculationResult(value, operation);
            
            // Assert
            result.Value.Should().Be(value);
            result.Operation.Should().Be(operation);
            result.IsValid.Should().BeTrue();
            
            // Should be serializable
            var json = result.ToJson();
            json.Should().NotBeNullOrEmpty();
            
            // Should have readable string representation
            var str = result.ToString();
            str.Should().NotBeNullOrEmpty();
            str.Should().Contain(operation);
        }
    }
}