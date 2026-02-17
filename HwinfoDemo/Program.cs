using System;
using System.Collections.Generic;
using System.Globalization;
using System.Reflection;
using System.Threading;
using System.Linq;
using System.IO;
using System.Text.Json;
using Hwinfo.SharedMemory;

class Program
{
    class SensorInfo
    {
        public int Index;
        public string Label = "";
        public string Value = "";
        public string? Unit;
    }

    // Clase para estructurar la salida del JSON
    class ExportData
    {
        public double Value { get; set; }
        public string Unit { get; set; } = "";
    }

    static void Main()
    {
        var reader = new SharedMemoryReader();
        List<SensorInfo> sensors = new();

        int[] selected = { 21, 66, 114 };
        string outputPath = "../hwinfo.json";

        while (true)
        {
            try
            {
                var readings = reader.ReadLocal();

                // 🔹 Construcción inicial / Mapeo de sensores
                if (sensors.Count == 0)
                {
                    int idx = 0;
                    var seen = new HashSet<string>(StringComparer.OrdinalIgnoreCase);

                    foreach (var r in readings)
                    {
                        string? label = GetPropertyString(r, "Label", "Name", "Sensor", "Caption");
                        string? value = GetPropertyString(r, "Value", "CurValue", "Current", "DisplayValue");
                        string? unit = GetPropertyString(r, "Unit", "Units");

                        if (string.IsNullOrWhiteSpace(label) || string.IsNullOrWhiteSpace(value))
                            continue;

                        if (!seen.Add(label))
                            continue;

                        sensors.Add(new SensorInfo
                        {
                            Index = idx++,
                            Label = label,
                            Value = value,
                            Unit = unit ?? "" // Guardamos la unidad detectada
                        });
                    }
                }
                else
                {
                    // Actualizar valores en tiempo real
                    foreach (var s in sensors)
                    {
                        foreach (var r in readings)
                        {
                            string? label = GetPropertyString(r, "Label", "Name", "Sensor", "Caption");

                            if (!string.Equals(label, s.Label, StringComparison.OrdinalIgnoreCase))
                                continue;

                            s.Value = GetPropertyString(r, "Value", "CurValue", "Current", "DisplayValue") ?? s.Value;
                            // También actualizamos la unidad por si cambia (aunque es raro)
                            s.Unit = GetPropertyString(r, "Unit", "Units") ?? s.Unit;

                            break;
                        }
                    }
                }

                // EXPORTAR SENSORES SELECCIONADOS CON UNIDADES
                var export = new Dictionary<string, ExportData>();

                foreach (var s in sensors)
                {
                    
                    
                    foreach (var r in readings)
                    {
                        string? label = GetPropertyString(
                            r, "Label", "Name", "Sensor", "Caption"
                        );

                        if (!string.Equals(label, s.Label,
                            StringComparison.OrdinalIgnoreCase))
                            continue;

                        s.Value = GetPropertyString(
                            r, "Value", "CurValue", "Current", "DisplayValue"
                        ) ?? s.Value;

                        break;
                    }
                    if (TryParseToDouble(s.Value, out double val))
                    {
                        string key = $"hwinfo_" + SanitizeKey(s.Label);

                        export[key] = new ExportData 
                        { 
                            Value = val, 
                            Unit = s.Unit ?? "" 
                        };
                    }
                }

                File.WriteAllText(
                    outputPath,
                    JsonSerializer.Serialize(export, new JsonSerializerOptions { WriteIndented = true })
                );

                // 🖥️ Consola (debug)
                Console.Clear();
                Console.WriteLine($"Actualizado: {DateTime.Now:HH:mm:ss}");
                Console.WriteLine("------------------------------");
                foreach (var kv in export)
                    Console.WriteLine($"{kv.Key} = {kv.Value.Value} {kv.Value.Unit}");

            }
            catch (Exception ex)
            {
                Console.WriteLine($"Error: {ex.Message}");
            }

            Thread.Sleep(500);
        }
    }

    // ---------- helpers ----------

    static string SanitizeKey(string s)
    {
        return s.ToLowerInvariant()
                .Replace(" ", "_")
                .Replace("-", "_")
                .Replace(".", "")
                .Replace("/", "_");
    }

    static bool TryParseToDouble(string raw, out double result)
    {
        result = 0;
        if (string.IsNullOrWhiteSpace(raw)) return false;

        var cleaned = raw.Trim();
        int i = 0;

        for (; i < cleaned.Length; i++)
        {
            char c = cleaned[i];
            if (!(char.IsDigit(c) || c == '.' || c == ',' ||
                  c == '+' || c == '-' || c == 'E' || c == 'e'))
                break;
        }

        if (i > 0)
            cleaned = cleaned.Substring(0, i);

        cleaned = cleaned.Replace(',', '.');

        return double.TryParse(
            cleaned,
            NumberStyles.Float,
            CultureInfo.InvariantCulture,
            out result);
    }

    static string? GetPropertyString(object obj, params string[] propNames)
    {
        var type = obj.GetType();
        
        // 1. Buscar por nombres específicos pasados por parámetro
        foreach (var name in propNames)
        {
            var prop = type.GetProperty(name, BindingFlags.Public | BindingFlags.Instance | BindingFlags.IgnoreCase);
            if (prop != null)
            {
                var v = prop.GetValue(obj);
                if (v != null) return v.ToString();
            }
        }

        // 2. Búsqueda por coincidencia parcial si falla lo anterior
        foreach (var prop in type.GetProperties())
        {
            string n = prop.Name.ToLowerInvariant();
            if (n.Contains("unit") || n.Contains("label") || n.Contains("value"))
            {
                var v = prop.GetValue(obj);
                if (v != null) return v.ToString();
            }
        }

        return null;
    }
}