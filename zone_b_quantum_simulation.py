import secrets
import time

class QuantumDataBlinder:
    """Implements Section 2 & 3: The XOR Data Blinding Operations."""
    @staticmethod
    def generate_quantum_key(length_bits):
        return [secrets.randbelow(2) for _ in range(length_bits)]

    @staticmethod
    def execute_xor_blind(message_bits, key_bits):
        return [m ^ k for m, k in zip(message_bits, key_bits)]

    @staticmethod
    def string_to_bits(s):
        bits = []
        for char in s:
            bin_char = format(ord(char), '08b')
            bits.extend([int(b) for b in bin_char])
        return bits

    @staticmethod
    def bits_to_string(bits):
        chars = []
        for i in range(0, len(bits), 8):
            byte = bits[i:i+8]
            if len(byte) < 8: break
            char_code = int("".join(map(str, byte)), 2)
            chars.append(chr(char_code))
        return "".join(chars)

class UpgradedZoneBEnclave:
    def __init__(self, master_secret_key=421983002):
        self.master_secret = master_secret_key
        # Prime modulus chosen to be larger than the secret key
        self.prime_modulus = 999999937 
        self.active_shares = {}
        
    def generate_shares(self):
        # Generates a degree-8 polynomial (requires 9 points to reconstruct)
        # f(x) = secret + c_1*x^1 + c_2*x^2 ... + c_8*x^8
        coefficients = [secrets.randbelow(self.prime_modulus) for _ in range(8)]
        for x in range(1, 16):
            y = self.master_secret
            for degree, coef in enumerate(coefficients, start=1):
                y = (y + coef * pow(x, degree, self.prime_modulus)) % self.prime_modulus
            self.active_shares[x] = y

    def _lagrange_interpolate_at_zero(self, shares):
        """Mathematically reconstructs the secret at f(0) modulo p."""
        secret = 0
        x_coords = list(shares.keys())
        
        for i in x_coords:
            numerator = 1
            denominator = 1
            for j in x_coords:
                if i == j: continue
                numerator = (numerator * (-j)) % self.prime_modulus
                denominator = (denominator * (i - j)) % self.prime_modulus
            
            # Modular inverse calculation via Fermat's Little Theorem
            inv_denominator = pow(denominator, self.prime_modulus - 2, self.prime_modulus)
            lagrange_basis = (numerator * inv_denominator) % self.prime_modulus
            secret = (secret + shares[i] * lagrange_basis) % self.prime_modulus
            
        return secret

    def process_blinded_satellite_stream(self, trustee_id_inputs, blinded_payload, quantum_key):
        start_time = time.time()
        print("\n[ZONE B] Incoming encrypted satellite data stream detected...")
        
        # 1. Unblind data stream
        unblinded_bits = QuantumDataBlinder.execute_xor_blind(blinded_payload, quantum_key)
        recovered_string = QuantumDataBlinder.bits_to_string(unblinded_bits)
        print(f"[RECOVERED TELEMETRY STRING] {recovered_string}")
        
        # 2. Extract and compile active shares present in quorum submission
        received_shares = {tid: self.active_shares[tid] for tid in trustee_id_inputs if tid in self.active_shares}
        
        # Threshold Check
        if len(received_shares) < 9:
            print("[SECURITY ABORT] Insufficient quorum points to solve polynomial matrix.")
            self._flush_volatile_registers(unblinded_bits, received_shares)
            return False
            
        # 3. Execute math: Recover secret using Lagrange Interpolation
        print("[COMPUTING] Resolving Lagrange Polynomial across available coordinates...")
        recovered_secret = self._lagrange_interpolate_at_zero(received_shares)
        
        # 4. Enforce Volatile Memory Flush (Section 2/3 Guardrail)
        # Ensures registers flush within the 500ms security window
        execution_time_ms = (time.time() - start_time) * 1000
        if execution_time_ms > 500:
            print(f"[TIMEOUT ERROR] Execution took {execution_time_ms:.2f}ms. Registers forced zero.")
            self._flush_volatile_registers(unblinded_bits, received_shares)
            return False
            
        if recovered_secret != self.master_secret:
            print("[SECURITY ALERT] Cryptographic secret mismatch. Unauthorized key validation.")
            self._flush_volatile_registers(unblinded_bits, received_shares)
            return False
            
        print(f"[SUCCESS] Reconstructed Secret: {recovered_secret} matches Master Root.")
        print(f"[SUCCESS] Token authorized within safe window ({execution_time_ms:.2f}ms).")
        
        self._flush_volatile_registers(unblinded_bits, received_shares)
        return True

    def _flush_volatile_registers(self, bit_array, share_dict):
        """Explicitly overwrites volatile structures to prevent cold-boot leakage."""
        print("[FLUSH] Overwriting volatile memory channels and clearing registers...")
        # Overwrite list elements directly in memory
        for i in range(len(bit_array)):
            bit_array[i] = 0
        # Clear dictionary contexts
        share_dict.clear()
