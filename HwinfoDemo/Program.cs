using System;
using System.Collections.Generic;
using System.Globalization;
using System.Reflection;
using System.Threading;
using Hwinfo.SharedMemory;

class Program
{
    static void Main()
    {
        var reader = new SharedMemoryReader();

        while (true)
        {
            try
            {
                var readings = reader.ReadLocal();

                // Construimos un diccionario label -> raw value (string) para búsquedas tolerantes
                var dict = new Dictionary<string, string>(StringComparer.OrdinalIgnoreCase);

                foreach (var reading in readings)
                {
                    string? label = GetPropertyString(reading, "Label", "Name", "Sensor", "Caption");
                    string? value = GetPropertyString(reading, "Value", "CurValue", "Current", "DisplayValue");

                    if (!string.IsNullOrEmpty(label) && !string.IsNullOrEmpty(value))
                    {
                        if (!dict.ContainsKey(label!))
                            dict[label!] = value!;
                    }
                }

                // Buscamos las tres métricas
                string? powerValue = FindByKeywords(dict, new[] {
                    "package power", "cpu package power", "cpu package", "cpu package watt", "power [w]", "power"
                });

                string? tempValue = FindByKeywords(dict, new[] {
                    "package temp", "cpu package temp", "cpu package temperature",
                    "package temperature", "temp", "temperature"
                });

                string? freqValue = FindByKeywords(dict, new[] {
                    "package clock", "cpu package clock",
                    "cpu frequency", "cpu clock", "clock", "freq", "mhz"
                });

                // Mostrar resultados (parsing seguro a double cuando sea posible)
                Console.WriteLine("\n--- Resultados ---");

                if (!string.IsNullOrEmpty(powerValue) && TryParseToDouble(powerValue, out double p))
                    Console.WriteLine($"Potencia de paquete: {p:F2} W");
                else if (!string.IsNullOrEmpty(powerValue))
                    Console.WriteLine($"Potencia de paquete (raw): {powerValue}");
                else
                    Console.WriteLine("Potencia de paquete: NO ENCONTRADA");

                if (!string.IsNullOrEmpty(tempValue) && TryParseToDouble(tempValue, out double t))
                    Console.WriteLine($"Temperatura de paquete: {t:F1} °C");
                else if (!string.IsNullOrEmpty(tempValue))
                    Console.WriteLine($"Temperatura de paquete (raw): {tempValue}");
                else
                    Console.WriteLine("Temperatura de paquete: NO ENCONTRADA");

                if (!string.IsNullOrEmpty(freqValue) && TryParseToDouble(freqValue, out double f))
                {
                    if (f > 100000) f /= 1_000_000.0;  // Hz → MHz
                    else if (f > 10000) f /= 1000.0;  // kHz → MHz

                    Console.WriteLine($"Frecuencia (aprox): {f:F0} MHz");
                }
                else if (!string.IsNullOrEmpty(freqValue))
                    Console.WriteLine($"Frecuencia (raw): {freqValue}");
                else
                    Console.WriteLine("Frecuencia: NO ENCONTRADA");

                Console.WriteLine("------------------");
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Error leyendo HWiNFO shared memory: {ex.Message}");
            }

            Thread.Sleep(3000); // <-- Ejecutar cada 3 segundos
        }
    }

    // Intenta obtener el primer property disponible entre los nombres dados, como string
    static string? GetPropertyString(object obj, params string[] propNames)
    {
        foreach (var name in propNames)
        {
            var prop = obj.GetType().GetProperty(name, BindingFlags.Public | BindingFlags.Instance | BindingFlags.IgnoreCase);
            if (prop != null)
            {
                var v = prop.GetValue(obj);
                if (v != null)
                    return v.ToString();
            }
        }

        foreach (var prop in obj.GetType().GetProperties())
        {
            if (prop.Name.IndexOf("label", StringComparison.OrdinalIgnoreCase) >= 0 ||
                prop.Name.IndexOf("name", StringComparison.OrdinalIgnoreCase) >= 0 ||
                prop.Name.IndexOf("sensor", StringComparison.OrdinalIgnoreCase) >= 0)
            {
                var v = prop.GetValue(obj);
                if (v != null) return v.ToString();
            }
            if (prop.Name.IndexOf("value", StringComparison.OrdinalIgnoreCase) >= 0 ||
                prop.Name.IndexOf("cur", StringComparison.OrdinalIgnoreCase) >= 0 ||
                prop.Name.IndexOf("display", StringComparison.OrdinalIgnoreCase) >= 0)
            {
                var v = prop.GetValue(obj);
                if (v != null) return v.ToString();
            }
        }

        return null;
    }

    // Busca en el diccionario una clave que contenga cualquiera de las keywords (ordenadas por prioridad)
    static string? FindByKeywords(Dictionary<string, string> dict, string[] keywords)
    {
        foreach (var kw in keywords)
            foreach (var kv in dict)
                if (kv.Key.Equals(kw, StringComparison.OrdinalIgnoreCase))
                    return kv.Value;

        foreach (var kw in keywords)
            foreach (var kv in dict)
                if (kv.Key.IndexOf(kw, StringComparison.OrdinalIgnoreCase) >= 0)
                    return kv.Value;

        var tokens = new List<string>();
        foreach (var k in keywords)
            tokens.AddRange(k.Split(new[] { ' ', '[', ']', '_', '-' }, StringSplitOptions.RemoveEmptyEntries));

        foreach (var kv in dict)
        {
            string key = kv.Key.ToLowerInvariant();
            foreach (var t in tokens)
            {
                var tt = t.ToLowerInvariant();
                if (tt.Length < 2) continue;
                if (key.Contains(tt))
                    return kv.Value;
            }
        }

        return null;
    }

    // Try parse flexible to double (acepta valores con unidades)
    static bool TryParseToDouble(string raw, out double result)
    {
        result = 0;
        if (string.IsNullOrWhiteSpace(raw)) return false;

        var cleaned = raw.Trim();
        int i = 0;

        for (i = 0; i < cleaned.Length; i++)
        {
            char c = cleaned[i];
            if (!(char.IsDigit(c) || c == '.' || c == ',' || c == '+' || c == '-' || c == 'E' || c == 'e'))
                break;
        }

        if (i > 0)
            cleaned = cleaned.Substring(0, i);

        cleaned = cleaned.Replace(',', '.');

        return double.TryParse(cleaned, NumberStyles.Float, CultureInfo.InvariantCulture, out result);
    }
}
