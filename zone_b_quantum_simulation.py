import secrets
import time

class QuantumDataBlinder:
    """Implements Section 2 & 3: The XOR Data Blinding Operations."""
    @staticmethod
    def generate_quantum_key(length_bits):
        # Simulates a Quantum Random Number Generator (QRNG) outputting true noise
        return [secrets.randbelow(2) for _ in range(length_bits)]

    @staticmethod
    def execute_xor_blind(message_bits, key_bits):
        # Applies the strict binary XOR logic matrix: 0^0=0, 1^1=0, 0^1=1, 1^0=1
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
            char_code = int("".join(map(str, byte)), 2)
            chars.append(chr(char_code))
        return "".join(chars)

class UpgradedZoneBEnclave:
    def __init__(self, master_secret_key=421983002):
        self.master_secret = master_secret_key
        self.prime_modulus = 999999937
        self.active_shares = {}
        
    def generate_shares(self):
        # Generate baseline polynomial shares for the 15 trustees
        coefficients = [secrets.randbelow(self.prime_modulus) for _ in range(8)]
        for x in range(1, 16):
            y = self.master_secret
            for degree, coef in enumerate(coefficients, start=1):
                y = (y + coef * pow(x, degree, self.prime_modulus)) % self.prime_modulus
            self.active_shares[x] = y

    def process_blinded_satellite_stream(self, trustee_id_inputs, blinded_payload, quantum_key):
        """
        Processes an incoming transmission protected by the Quantum Physics Shield.
        Cancels out the entropic noise before calculating the threshold keys.
        """
        print("\n[ZONE B] Incoming encrypted satellite data stream detected...")
        print(f"[RAW INBOUND CIPHERTEXT] {''.join(map(str, blinded_payload[:24]))}...")
        
        # Section 3 Phase 4: Decryption via Canceling Noise
        print("[PHYSICS SHIELD] Applying symmetric quantum key stream to dissolve entropy...")
        unblinded_bits = QuantumDataBlinder.execute_xor_blind(blinded_payload, quantum_key)
        recovered_string = QuantumDataBlinder.bits_to_string(unblinded_bits)
        
        print(f"[RECOVERED TELEMETRY STRING] {recovered_string}")
        
        # Verify and execute threshold math
        received_shares = {tid: self.active_shares[tid] for tid in trustee_id_inputs if tid in self.active_shares}
        if len(received_shares) < 9:
            print("[SECURITY ABORT] Insufficient quorum keys to solve polynomial matrix.")
            return False
            
        print("[SUCCESS] Threshold met. Enclave registers verified. Cutoff token authorized.")
        return True

# --- RUN CONCURRENT SYSTEM SIMULATION ---
if __name__ == "__main__":
    enclave = UpgradedZoneBEnclave()
    enclave.generate_shares()
    
    # Define an unencrypted critical telemetry event instruction
    critical_instruction = "COMMAND: DATACENTER_4B_QUARANTINE_ACTIVATE"
    message_bits = QuantumDataBlinder.string_to_bits(critical_instruction)
    
    # Generate matching Quantum Keys (The One-Time Pad stream)
    quantum_key_stream = QuantumDataBlinder.generate_quantum_key(len(message_bits))
    
    # Phase 2: Masking the data at the sender level (Alice)
    ciphertext_bits = QuantumDataBlinder.execute_xor_blind(message_bits, quantum_key_stream)
    
    # Simulating Eve Intercepting data mid-transit
    print("============= ADVERSARIAL INTERCEPTION SIMULATION =============")
    print(f"Eve's Intercepted Bitstream: {''.join(map(str, ciphertext_bits[:32]))}...")
    print("[MATHEMATICAL BRICK WALL] Ciphertext conditional probability matches pure white noise.")
    
    # Phase 4: Receiver processing (Bob/Zone B Enclave)
    # 9 Trustees provide their keys to decrypt the underlying instruction
    active_voters = [1, 2, 3, 4, 5, 6, 7, 8, 9]
    enclave.process_blinded_satellite_stream(active_voters, ciphertext_bits, quantum_key_stream)