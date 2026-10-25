using System;
using System.Collections;
using System.Collections.Generic;
using System.Diagnostics;
using System.Linq;
using System.Security.Cryptography;
using System.Text;

namespace ProjectCaesura
{
    public static class QuantumDataBlinder
    {
        // Section 3: Simulates a Quantum Random Number Generator (QRNG)
        public static BitArray GenerateQuantumKey(int lengthBits)
        {
            var bits = new BitArray(lengthBits);
            for (int i = 0; i < lengthBits; i++)
            {
                // RandomNumberGenerator is cryptographically secure (like secrets in Python)
                bits[i] = RandomNumberGenerator.GetInt32(2) == 1;
            }
            return bits;
        }

        // Applies strict binary XOR data blinding matrix
        public static BitArray ExecuteXorBlind(BitArray message, BitArray key)
        {
            // Creates a copy and applies the bitwise XOR operator
            var result = new BitArray(message);
            return result.Xor(key);
        }

        public static BitArray StringToBits(string input)
        {
            byte[] bytes = Encoding.UTF8.GetBytes(input);
            return new BitArray(bytes);
        }

        public static string BitsToString(BitArray bits)
        {
            // Convert BitArray back to a standard byte array
            byte[] bytes = new byte[(bits.Length + 7) / 8];
            bits.CopyTo(bytes, 0);
            return Encoding.UTF8.GetString(bytes).TrimEnd('\0');
        }
    }

    public class UpgradedZoneBEnclave
    {
        private readonly long _masterSecret;
        // Prime modulus larger than the secret key
        private readonly long _primeModulus = 999999937; 
        private readonly Dictionary<int, long> _activeShares = new();

        public UpgradedZoneBEnclave(long masterSecretKey = 421983002)
        {
            _masterSecret = masterSecretKey;
        }

        public void GenerateShares()
        {
            // Generates a degree-8 polynomial (requires 9 points to reconstruct)
            long[] coefficients = new long[8];
            for (int i = 0; i < 8; i++)
            {
                coefficients[i] = RandomNumberGenerator.GetInt32(1, (int)_primeModulus);
            }

            for (int x = 1; x <= 15; x++)
            {
                long y = _masterSecret;
                for (int degree = 1; degree <= 8; degree++)
                {
                    long coef = coefficients[degree - 1];
                    long term = (coef * ModPow(x, degree, _primeModulus)) % _primeModulus;
                    y = (y + term) % _primeModulus;
                }
                _activeShares[x] = y;
            }
        }

        // Section 3 Phase 4: Processes incoming blinded telemetry payload
        public bool ProcessBlindedSatelliteStream(List<int> trusteeIds, BitArray blindedPayload, BitArray quantumKey)
        {
            var stopwatch = Stopwatch.StartNew();
            Console.WriteLine("\n[ZONE B] Incoming encrypted satellite data stream detected...");

            // 1. Cancel out entropic noise using the symmetric Quantum Pad
            BitArray unblindedBits = QuantumDataBlinder.ExecuteXorBlind(blindedPayload, quantumKey);
            string recoveredString = QuantumDataBlinder.BitsToString(unblindedBits);
            Console.WriteLine($"[RECOVERED TELEMETRY STRING] {recoveredString}");

            // 2. Isolate submitted keys from the trust matrix
            var receivedShares = new Dictionary<int, long>();
            foreach (var id in trusteeIds)
            {
                if (_activeShares.TryGetValue(id, out long shareValue))
                {
                    receivedShares[id] = shareValue;
                }
            }

            // Quorum Check
            if (receivedShares.Count < 9)
            {
                Console.WriteLine("[SECURITY ABORT] Insufficient quorum keys to solve polynomial matrix.");
                FlushVolatileRegisters(unblindedBits, receivedShares);
                return false;
            }

            // 3. Resolve Lagrange Polynomial Interpolation to find f(0)
            Console.WriteLine("[COMPUTING] Resolving Lagrange Polynomial across available coordinates...");
            long recoveredSecret = LagrangeInterpolateAtZero(receivedShares);

            // 4. Enforce 500ms Volatile Register Flush Guardrail
            stopwatch.Stop();
            double executionTimeMs = stopwatch.Elapsed.TotalMilliseconds;

            if (executionTimeMs > 500.0)
            {
                Console.WriteLine($"[TIMEOUT ERROR] Execution took {executionTimeMs:F2}ms. Microcode expired.");
                FlushVolatileRegisters(unblindedBits, receivedShares);
                return false;
            }

            if (recoveredSecret != _masterSecret)
            {
                Console.WriteLine("[SECURITY ALERT] Cryptographic secret mismatch. Unauthorized footprint.");
                FlushVolatileRegisters(unblindedBits, receivedShares);
                return false;
            }

            Console.WriteLine($"[SUCCESS] Reconstructed Secret: {recoveredSecret} matches Master Root.");
            Console.WriteLine($"[SUCCESS] Token authorized within safe window ({executionTimeMs:F4}ms).");

            FlushVolatileRegisters(unblindedBits, receivedShares);
            return true;
        }

        private long LagrangeInterpolateAtZero(Dictionary<int, long> shares)
        {
            long secret = 0;
            var xCoords = shares.Keys.ToList();

            foreach (var i in xCoords)
            {
                long numerator = 1;
                long denominator = 1;

                foreach (var j in xCoords)
                {
                    if (i == j) continue;
                    numerator = (numerator * (-j)) % _primeModulus;
                    denominator = (denominator * (i - j)) % _primeModulus;
                }

                // Handle negative values resulting from modulo arithmetic
                if (numerator < 0) numerator += _primeModulus;
                if (denominator < 0) denominator += _primeModulus;

                // Modular Inverse via Fermat's Little Theorem
                long invDenominator = ModPow(denominator, _primeModulus - 2, _primeModulus);
                long lagrangeBasis = (numerator * invDenominator) % _primeModulus;

                long term = (shares[i] * lagrangeBasis) % _primeModulus;
                secret = (secret + term) % _primeModulus;
            }

            return secret;
        }

        private void FlushVolatileRegisters(BitArray bitArray, Dictionary<int, long> shareDict)
        {
            Console.WriteLine("[FLUSH] Overwriting volatile memory channels and clearing registers...");
            // Hard zeroing memory structures to stop physical cold-boot reading attacks
            bitArray.SetAll(false);
            shareDict.Clear();
        }

        private static long ModPow(long value, long exponent, long modulus)
        {
            return (long)System.Numerics.BigInteger.ModPow(value, exponent, modulus);
        }
    }

    class Program
    {
        static void Main()
        {
            var enclave = new UpgradedZoneBEnclave();
            enclave.GenerateShares();

            string instruction = "COMMAND: DATACENTER_4B_QUARANTINE_ACTIVATE";
            BitArray messageBits = QuantumDataBlinder.StringToBits(instruction);
            BitArray quantumKey = QuantumDataBlinder.GenerateQuantumKey(messageBits.Length);

            // Encrypt data to send across the network
            BitArray ciphertext = QuantumDataBlinder.ExecuteXorBlind(messageBits, quantumKey);

            Console.WriteLine("============= ADVERSARIAL INTERCEPTION SIMULATION =============");
            Console.WriteLine("[MATHEMATICAL BRICK WALL] Ciphertext conditional probability matches white noise.");

            // Process payload via 9 active trustees
            var activeVoters = new List<int> { 1, 2, 3, 4, 5, 6, 7, 8, 9 };
            enclave.ProcessBlindedSatelliteStream(activeVoters, ciphertext, quantumKey);
        }
    }
}
