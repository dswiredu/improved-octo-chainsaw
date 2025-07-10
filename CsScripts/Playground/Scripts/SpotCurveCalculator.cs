using System.Globalization;
using ClosedXML.Excel;

namespace Playground.Scripts;

public static class SpotCurveCalculator
{
    private static readonly Dictionary<string, int> TenorToMonthCurves = new()
    {
        { "TSY_1M", 1 },
        { "TSY_3M", 3 },
        { "TSY_6M", 6 },
        { "TSY_1Y", 12 },
        { "TSY_2Y", 24 },
        { "TSY_3Y", 36 },
        { "TSY_5Y", 60 },
        { "TSY_7Y", 84 },
        { "TSY_10Y", 120 },
        { "TSY_30Y", 360 }
    };

    private static readonly Dictionary<string, int> TenorToMonthsTreasury = new()
    {
        { "1 Mo", 1 },
        { "2 Mo", 2 },
        { "3 Mo", 3 },
        { "4 Mo", 4 },
        { "6 Mo", 6 },
        { "1 Yr", 12 },
        { "2 Yr", 24 },
        { "3 Yr", 36 },
        { "5 Yr", 60 },
        { "7 Yr", 84 },
        { "10 Yr", 120 },
        { "20 Yr", 240 },
        { "30 Yr", 360 }
    };
    private static class IoHelper
    {
        public static Dictionary<int, double> ReadCurveRowFromExcel(string filePath)
        {
            if (!File.Exists(filePath))
                throw new FileNotFoundException("File not found", fileName: filePath);
            
            var result = new Dictionary<int, double>();
            using var workbook = new XLWorkbook(filePath);
            var sheet = workbook.Worksheet(name:"ag-grid");
            
            var headers = sheet.Row(3).Cells().Select(c => c.GetString().Trim()).ToList();  // third row is header
            var dataRow = sheet.Row(4);  // fourth row is first data row

            for (int i = 0; i < headers.Count; i++)
            {
                string header = headers[i];
                if (!TenorToMonthCurves.TryGetValue(header, out int months))
                    continue;
                double val = dataRow.Cell(i + 1).GetDouble(); // Excel is 1-indexed
                result[months] = val; // convert % annual → decimal monthly
            }
            return result;
        }
        
        public static List<double> ReadRates(string filePath, string columnName, bool monthly = false)
        {   
            if (!File.Exists(filePath))
                throw new FileNotFoundException("File not found", fileName: filePath);
            
            var lines = File.ReadAllLines(filePath);
            var headers = lines[0].Split(",").Select(x => x.Trim()).ToList();
            
            int index = headers.IndexOf(columnName);
            double denominator = monthly ? 12.0 : 1.0;
            
            if (index==-1)
                throw new IndexOutOfRangeException($"Column '{columnName}' not found");
            return lines
                .Skip(1)
                .Select(line =>
                {
                    var fields = line.Split(',');
                    if (double.TryParse(fields[index], NumberStyles.Any, CultureInfo.InvariantCulture, out double val))
                        return val / 100.0 / denominator;
                    return 0.0;
                })
                .ToList();
        }
        
        public static Dictionary<int, double> ReadRates(string filePath)
        {   
            if (!File.Exists(filePath))
                throw new FileNotFoundException("File not found", fileName: filePath);
            
            var lines = File.ReadAllLines(filePath);
            var headers = lines[0].Split(",").Select(x => x.Trim()).ToList();
            int dateIndex = headers.IndexOf("Date");
            int rateIndex = headers.IndexOf("Rates");

            if (dateIndex == -1 || rateIndex == -1)
                throw new Exception("CSV must contain 'Date' and 'Rates' columns.");

            var result = new Dictionary<int, double>();

            foreach (var line in lines.Skip(1))
            {
                var parts = line.Split(',').Select(x => x.Trim()).ToArray(); 
                if (parts.Length <= Math.Max(dateIndex, rateIndex))
                    continue;
                
                string dateStr = parts[dateIndex];
                string rateStr = parts[rateIndex];
                
                if (!TenorToMonthsTreasury.TryGetValue(dateStr, out int months))
                {
                    Console.WriteLine($"Skipping unknown tenor: {dateStr}");
                    continue;
                }
                
                if (double.TryParse(rateStr, out double rate))
                {
                    result[months] = rate;
                }
                else
                {
                    Console.WriteLine($"Skipping unparsable rate: {rateStr}");
                }
            }
            
            return result;
        }
        
        public static void WriteSpotCurveCsv(List<double> monthlyRates, string outputPath)
        {
            using var writer = new StreamWriter(outputPath);
            writer.WriteLine("Months,Rate");
            for (int i = 0; i < monthlyRates.Count; i++)
            {
                writer.WriteLine(string.Join(",", i + 1, monthlyRates[i]));
            }
        }
        
        public static void WriteSpotCurveCsv(
            List<double> fwdRates,
            List<double> spotMonthly,
            List<double> spotContinuous,
            List<double> spotEar,
            string outputPath)
        {
            using var writer = new StreamWriter(outputPath);
            writer.WriteLine("TSY_1M,Spot_MonthlyCompounded,Spot_Continuous,Spot_EAR");

            for (int i = 0; i < fwdRates.Count; i++)
            {
                double tsy = fwdRates[i] * 12.0 * 100.0;
                writer.WriteLine(string.Join(",",
                    tsy.ToString("F6", CultureInfo.InvariantCulture),
                    (spotMonthly[i] * 100.0).ToString("F6", CultureInfo.InvariantCulture),
                    (spotContinuous[i] * 100.0).ToString("F6", CultureInfo.InvariantCulture),
                    (spotEar[i] * 100.0).ToString("F6", CultureInfo.InvariantCulture)
                ));
            }
        }
    }

    private static List<double> LinearlyInterpolateCurve(Dictionary<int, double> knownPoints, int totalMonths)
    {
        var sortedKeys = knownPoints.Keys.OrderBy(k => k).ToList();
        var interpolated = new List<double>();

        for (int m = 1; m <= totalMonths; m++)
        {
            if (knownPoints.TryGetValue(m, out double knownValue))
            {
                interpolated.Add(knownValue);
                continue;
            }
            // Find left and right anchors for interpolation
            int left = sortedKeys.LastOrDefault(k => k < m);
            int right = sortedKeys.FirstOrDefault(k => k > m);

            if (left == 0 || right == 0)
            {
                // Out-of-bounds: flat extrapolation (extend the nearest value)
                double edgeRate = knownPoints.TryGetValue(left, out double leftValue) ? leftValue : knownPoints[right];
                interpolated.Add(edgeRate);
            }
            else
            {
                double r1 = knownPoints[left];
                double r2 = knownPoints[right];

                // Linear interpolation formula
                double interpolatedRate = r1 + (r2 - r1) * ((double)(m - left) / (right - left));
                interpolated.Add(interpolatedRate);
            }
        }
        return interpolated;
    }
    
    private static List<double> ComputeSpotMonthlyCompounded(List<double> fwdRates)
    {
        List<double> spotMonthlyCompounded = new List<double>();
        double compounded = 1.0;

        for (int i = 0; i < fwdRates.Count; i++)
        {
            compounded *= (1 + fwdRates[i]);
            int n = i + 1;
            double spot = Math.Pow(compounded, 12.0/n) - 1.0;
            spotMonthlyCompounded.Add(spot);
        }

        return spotMonthlyCompounded;
    }

    private static List<double> ComputeSpotContinuous(List<double> fwdRates)
    {
        var spotRates = new List<double>();
        double cumulativeLogSum = 0.0;

        for (int i = 0; i < fwdRates.Count; i++)
        {
            double fwd = fwdRates[i];
            cumulativeLogSum += Math.Log(1.0 + fwd);
            int n = i + 1;
            double spot = (cumulativeLogSum / n) * 12.0;
            spotRates.Add(spot);
        }

        return spotRates;
    }
    
    private static List<double> ComputeSpotEAR(List<double> fwdRates)
    {
        var spotRates = new List<double>();
        double compounded = 1.0;

        for (int i = 0; i < fwdRates.Count; i++)
        {
            compounded *= (1.0 + fwdRates[i]);
            int n = i + 1;
            double spot = Math.Pow(compounded, 1.0 / (n / 12.0)) - 1.0;
            spotRates.Add(spot);
        }

        return spotRates;
    }

    /// <summary>
    /// Bootstraps spot rates from a list of interpolated monthly annualized yields.
    /// Assumes monthly compounding.
    /// </summary>
    /// <param name="monthlyAnnualYields">List of annualized yield rates in percent (e.g., 4.33 means 4.33%)</param>
    /// <returns>List of spot rates in percent (annualized) for each month</returns>
    public static List<double> BootstrapSpotsFromYields(List<double> monthlyAnnualYields)
    {
        var spotRates = new List<double>();
        var discountFactors = new List<double>();

        for (int t = 1; t <= monthlyAnnualYields.Count; t++)
        {
            double annualYield = monthlyAnnualYields[t - 1] / 100.0;   // Convert percent to decimal
            double monthlyRate = annualYield / 12.0;

            if (t == 1)
            {
                // First month: DF_1 = 1 / (1 + r/12)
                double df1 = 1.0 / (1.0 + monthlyRate);
                discountFactors.Add(df1);
            }
            else
            {
                // DF_t = (1 - (sum of previous DFs) * r/12) / (1 + r/12)
                double sumPriorDFs = 0.0;
                for (int i = 0; i < t - 1; i++)
                    sumPriorDFs += discountFactors[i];

                double df = (1.0 - sumPriorDFs * monthlyRate) / (1.0 + monthlyRate);
                discountFactors.Add(df);
            }

            // s_t = 12 * ((1 / DF_t)^(1 / t) - 1)
            double dfT = discountFactors[t - 1];
            double spot = 12.0 * (Math.Pow(1.0 / dfT, 1.0 / t) - 1.0);
            spotRates.Add(spot * 100.0); // Convert back to percent
        }

        return spotRates;
    }

    
    private static (List<double> Monthly, List<double> Continuous, List<double> EAR)
        ComputeAllSpots(List<double> fwdRates)
    {
        var monthly = ComputeSpotMonthlyCompounded(fwdRates);
        var continuous = ComputeSpotContinuous(fwdRates);
        var ear = ComputeSpotEAR(fwdRates);
        return (monthly, continuous, ear);
    }

    public static void Run()
    {
        string path = @"C:\Users\dwiredu\OneDrive - AGAM CAPITAL MANAGEMENT, LLC\Documents\quant\clients\guardian\DataforResiMortgage_new";
        string inputFile = Path.Combine(path, "us-treasury-yields.csv");
        string spotCurveOutPath = Path.Combine(path, "yields-interpolated.csv");
        Dictionary<int, double> yieldRates = IoHelper.ReadRates(inputFile);
        List<double> monthlyRates = LinearlyInterpolateCurve(yieldRates, totalMonths:360);
        var spotCurve = BootstrapSpotsFromYields(monthlyRates);
        IoHelper.WriteSpotCurveCsv(spotCurve, spotCurveOutPath);
    }
}