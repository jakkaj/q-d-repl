using System;
using Newtonsoft.Json;

namespace Calculator.Models
{
    /// <summary>
    /// Represents the result of a mathematical calculation
    /// </summary>
    public class CalculationResult
    {
        public double Value { get; set; }
        public string Operation { get; set; } = string.Empty;
        public DateTime Timestamp { get; set; }
        public bool IsValid { get; set; }
        public string? ErrorMessage { get; set; }

        public CalculationResult()
        {
            Timestamp = DateTime.UtcNow;
        }

        public CalculationResult(double value, string operation) : this()
        {
            Value = value;
            Operation = operation;
            IsValid = true;
        }

        public static CalculationResult Error(string message)
        {
            return new CalculationResult
            {
                IsValid = false,
                ErrorMessage = message,
                Value = 0,
                Operation = "error"
            };
        }

        public string ToJson()
        {
            return JsonConvert.SerializeObject(this, Formatting.Indented);
        }

        public override string ToString()
        {
            if (!IsValid)
                return $"Error: {ErrorMessage}";
            
            return $"{Operation} = {Value:F2} (at {Timestamp:yyyy-MM-dd HH:mm:ss})";
        }
    }
}