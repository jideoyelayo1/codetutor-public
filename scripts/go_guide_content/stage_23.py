STAGE = '23 · Cryptography'
PKG = 'https://pkg.go.dev/'


def f(path, content):
    return dict(path=path, content=content)


LESSONS = [
dict(key='crypto-hashes', stage=STAGE, title='Cryptographic hashes: SHA-2, SHA-3 and the legacy MD5/SHA-1',
body=[
'A cryptographic hash maps any input to a fixed-size digest such that finding two inputs with the same digest, or an input for a given digest, is infeasible. crypto/sha256 and crypto/sha512 (SHA-2) and crypto/sha3 (SHA-3, plus the SHAKE extendable-output functions) are the current choices. Each offers a one-shot Sum function and a streaming hash.Hash from New.',
'crypto/md5 and crypto/sha1 are broken for collision resistance: attackers can craft two documents with the same digest. Keep them only for compatibility, such as legacy checksums or Git object names, never for signatures or integrity against attackers.',
'Package crypto names algorithms with crypto.Hash constants (crypto.SHA256, crypto.SHA3_256) and links them to implementations; Available reports whether an implementation is linked in. Signature APIs take these constants to say which hash was used.',
],
code=r'''package main

import (
    "crypto"
    "crypto/md5"
    "crypto/sha1"
    "crypto/sha256"
    "crypto/sha3"
    "crypto/sha512"
    "fmt"
    "io"
    "strings"
)

func main() {
    data := []byte("abc")
    fmt.Printf("%x\n", sha256.Sum256(data))
    fmt.Printf("%x\n", sha512.Sum512_256(data))
    fmt.Printf("%x\n", sha3.Sum256(data))
    fmt.Printf("%x\n", sha3.SumSHAKE128(data, 8))
    fmt.Printf("%x %x\n", md5.Sum(data), sha1.Sum(data))
    h := crypto.SHA256.New()
    io.Copy(h, strings.NewReader("abc"))
    fmt.Println(h.Size(), fmt.Sprintf("%x", h.Sum(nil)) == fmt.Sprintf("%x", sha256.Sum256(data)), crypto.SHA3_256.Available())
}
''',
expectedStdout='ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad\n53048e2681941ef99b2e29b76b4c7dabe4c2d0c634fc6d46e0e2f13107e7af23\n3a985da74fe225b2045c172d6bd390bd855f086e3e9d525b46bfe24511431532\n5881092dd818bf5c\n900150983cd24fb0d6963f7d28e17f72 a9993e364706816aba3e25717850c26c9cd0d89d\n32 true true\n',
challenge='Hash the file contents "line1\\nline2\\n" in two Write calls on a sha256 hash and show that the digest equals sha256.Sum256 of the whole text.',
solution=r'''package main

import (
    "crypto/sha256"
    "fmt"
)

func main() {
    h := sha256.New()
    h.Write([]byte("line1\n"))
    h.Write([]byte("line2\n"))
    whole := sha256.Sum256([]byte("line1\nline2\n"))
    fmt.Println(string(h.Sum(nil)) == string(whole[:]))
}
''',
solutionStdout='true\n',
question='Why must MD5 not be used to sign documents?',
correct='Collisions can be crafted, so two different documents can share one digest',
wrong=['MD5 digests are too long', 'MD5 is not available in Go'],
reasoning='A signature over an MD5 digest covers every document with that digest, and attackers can construct such pairs.',
sourceURL=PKG+'crypto/sha256',
additionalReadings=[dict(title='crypto/sha3', url=PKG+'crypto/sha3', section='SHA-3 and SHAKE')]),

dict(key='crypto-mac-kdf', stage=STAGE, title='HMAC, constant-time comparison, key derivation and secure randomness',
body=[
'crypto/hmac authenticates messages with a shared key: anyone without the key cannot produce a valid tag. Compare tags with hmac.Equal, which runs in constant time; a normal == leaks how many leading bytes matched through timing. crypto/subtle provides ConstantTimeCompare and related primitives for the same reason.',
'Key derivation turns secrets into keys. crypto/hkdf (Go 1.24) extracts and expands high-entropy secrets, such as a Diffie-Hellman result, into several independent keys with different info labels. crypto/pbkdf2 stretches low-entropy passwords with many iterations; for new password storage prefer a memory-hard function such as argon2 or bcrypt from golang.org/x/crypto.',
'crypto/rand is the only correct source of randomness for keys, nonces and tokens. rand.Read never fails on supported platforms since Go 1.24, and rand.Text returns a secure random string suitable for tokens.',
],
code=r'''package main

import (
    "crypto/hkdf"
    "crypto/hmac"
    "crypto/pbkdf2"
    "crypto/rand"
    "crypto/sha256"
    "crypto/subtle"
    "fmt"
)

func sign(key, msg []byte) []byte {
    m := hmac.New(sha256.New, key)
    m.Write(msg)
    return m.Sum(nil)
}

func main() {
    key := []byte("shared secret")
    tag := sign(key, []byte("transfer 10"))
    fmt.Printf("%x\n", tag[:8])
    fmt.Println(hmac.Equal(tag, sign(key, []byte("transfer 10"))), hmac.Equal(tag, sign(key, []byte("transfer 99"))))
    fmt.Println(subtle.ConstantTimeCompare([]byte("abc"), []byte("abd")))
    encKey, _ := hkdf.Key(sha256.New, []byte("dh-shared-secret"), []byte("salt"), "encryption", 32)
    macKey, _ := hkdf.Key(sha256.New, []byte("dh-shared-secret"), []byte("salt"), "authentication", 32)
    fmt.Println(len(encKey), string(encKey) != string(macKey))
    stretched, _ := pbkdf2.Key(sha256.New, "correct horse", []byte("salt"), 600_000, 32)
    fmt.Printf("%x\n", stretched[:8])
    token := rand.Text()
    fmt.Println(len(token))
}
''',
expectedStdout='e96b6922a44c85b0\ntrue false\n0\n32 true\na1c77ee2d2bb7e53\n26\n',
challenge='Write func verify(key, msg, tag []byte) bool using hmac.Equal and show it accepts the right tag and rejects a tag with one flipped bit.',
solution=r'''package main

import (
    "crypto/hmac"
    "crypto/sha256"
    "fmt"
)

func tag(key, msg []byte) []byte {
    m := hmac.New(sha256.New, key)
    m.Write(msg)
    return m.Sum(nil)
}

func verify(key, msg, t []byte) bool { return hmac.Equal(t, tag(key, msg)) }

func main() {
    k, msg := []byte("k"), []byte("hello")
    good := tag(k, msg)
    bad := append([]byte(nil), good...)
    bad[0] ^= 1
    fmt.Println(verify(k, msg, good), verify(k, msg, bad))
}
''',
solutionStdout='true false\n',
question='Why compare MAC tags with hmac.Equal instead of bytes.Equal?',
correct='hmac.Equal takes the same time regardless of where bytes differ, so timing reveals nothing',
wrong=['bytes.Equal cannot compare 32-byte slices', 'hmac.Equal also checks the key'],
reasoning='bytes.Equal can return at the first mismatch. Measuring that lets an attacker guess a valid tag byte by byte.',
sourceURL=PKG+'crypto/hmac',
additionalReadings=[dict(title='crypto/hkdf', url=PKG+'crypto/hkdf', section='Key'), dict(title='crypto/rand.Text', url=PKG+'crypto/rand#Text', section='Text')]),

dict(key='crypto-aead', stage=STAGE, title='Authenticated encryption: AES-GCM, and why DES and RC4 are legacy',
body=[
'Use authenticated encryption (AEAD): it provides confidentiality and detects any modification. crypto/aes provides the AES block cipher and crypto/cipher wraps it in modes; cipher.NewGCM gives AES-GCM. Seal encrypts and appends a tag; Open verifies the tag before returning any plaintext and fails on any tampering.',
'A GCM nonce must never repeat for the same key, or security collapses. Generate random 12-byte nonces from crypto/rand, or use cipher.NewGCMWithRandomNonce (Go 1.24), which manages them for you. Additional data, such as a header, is authenticated but not encrypted.',
'crypto/des (including triple DES) and crypto/rc4 remain for interoperability with old systems only: DES keys are brute-forceable, 3DES has a 64-bit block that leaks over large data, and RC4 has statistical biases. Never choose them for new designs.',
],
code=r'''package main

import (
    "crypto/aes"
    "crypto/cipher"
    "crypto/des"
    "crypto/rc4"
    "fmt"
)

func main() {
    key := make([]byte, 32)
    block, _ := aes.NewCipher(key)
    aead, _ := cipher.NewGCMWithRandomNonce(block)
    sealed := aead.Seal(nil, nil, []byte("secret message"), []byte("header"))
    fmt.Println(len(sealed), aead.Overhead())
    plain, err := aead.Open(nil, nil, sealed, []byte("header"))
    fmt.Println(string(plain), err)
    sealed[len(sealed)-1] ^= 1
    _, err = aead.Open(nil, nil, sealed, []byte("header"))
    fmt.Println(err)
    _, err = aead.Open(nil, nil, sealed, []byte("other header"))
    fmt.Println(err != nil)
    d, _ := des.NewTripleDESCipher(make([]byte, 24))
    r, _ := rc4.NewCipher([]byte("legacy"))
    fmt.Println(d.BlockSize(), r != nil)
}
''',
expectedStdout='42 28\nsecret message <nil>\ncipher: message authentication failed\ntrue\n8 true\n',
challenge='Encrypt "a" and then "a" again with the same NewGCMWithRandomNonce AEAD and print whether the two ciphertexts differ (they should, because the nonce is random).',
solution=r'''package main

import (
    "bytes"
    "crypto/aes"
    "crypto/cipher"
    "fmt"
)

func main() {
    block, _ := aes.NewCipher(make([]byte, 16))
    aead, _ := cipher.NewGCMWithRandomNonce(block)
    a := aead.Seal(nil, nil, []byte("a"), nil)
    b := aead.Seal(nil, nil, []byte("a"), nil)
    fmt.Println(!bytes.Equal(a, b))
}
''',
solutionStdout='true\n',
question='What happens if a GCM nonce is reused with the same key?',
correct='Confidentiality and authenticity both break; an attacker can forge messages',
wrong=['Only the two messages become linkable', 'Nothing; GCM tolerates repeats'],
reasoning='GCM is a stream construction. Reuse reveals the XOR of plaintexts and the authentication key, which enables forgeries.',
sourceURL=PKG+'crypto/cipher#NewGCMWithRandomNonce',
additionalReadings=[dict(title='crypto/aes', url=PKG+'crypto/aes', section='NewCipher')]),

dict(key='crypto-signatures', stage=STAGE, title='Digital signatures: Ed25519, ECDSA, RSA-PSS and crypto.Signer',
body=[
'A signature proves that the holder of a private key approved a message, and anyone with the public key can check it. crypto/ed25519 is the simplest safe choice: fixed-size keys and signatures, deterministic, fast. crypto/ecdsa with P-256 is required by many standards; crypto/rsa with PSS padding (or PKCS #1 v1.5 for legacy) is ubiquitous. New RSA keys should be at least 2048 bits; since Go 1.24, keys smaller than 1024 bits are rejected by default (GODEBUG=rsa1024min=0 restores them for legacy tests).',
'All of them implement crypto.Signer: Public() and Sign(rand, digest, opts). Code that only needs to sign, such as TLS or a hardware key, depends on crypto.Signer rather than a concrete key type.',
'crypto/elliptic exposes the NIST curves\' parameters; its low-level point arithmetic is deprecated in favour of crypto/ecdh and crypto/ecdsa. crypto/dsa is deprecated and insecure at its common sizes; it remains only to verify old signatures.',
],
code=r'''package main

import (
    "crypto"
    "crypto/dsa"
    "crypto/ecdsa"
    "crypto/ed25519"
    "crypto/elliptic"
    "crypto/rand"
    "crypto/rsa"
    "crypto/sha256"
    "fmt"
)

func check(s crypto.Signer, verify func([]byte, []byte) bool, digest []byte, opts crypto.SignerOpts) bool {
    sig, err := s.Sign(rand.Reader, digest, opts)
    return err == nil && verify(digest, sig)
}

func main() {
    msg := []byte("release v1.27")
    pub, priv, _ := ed25519.GenerateKey(nil)
    sig := ed25519.Sign(priv, msg)
    fmt.Println(len(sig), ed25519.Verify(pub, msg, sig), ed25519.Verify(pub, []byte("tampered"), sig))
    digest := sha256.Sum256(msg)
    ec, _ := ecdsa.GenerateKey(elliptic.P256(), rand.Reader)
    fmt.Println(check(ec, func(d, s []byte) bool { return ecdsa.VerifyASN1(&ec.PublicKey, d, s) }, digest[:], crypto.SHA256))
    rk, _ := rsa.GenerateKey(rand.Reader, 2048)
    pss := &rsa.PSSOptions{Hash: crypto.SHA256}
    fmt.Println(check(rk, func(d, s []byte) bool { return rsa.VerifyPSS(&rk.PublicKey, crypto.SHA256, d, s, pss) == nil }, digest[:], pss))
    _, err := rsa.GenerateKey(rand.Reader, 512)
    fmt.Println(err != nil, elliptic.P256().Params().Name)
    var params dsa.Parameters
    fmt.Println(dsa.L1024N160 == 0, params.P == nil)
}
''',
expectedStdout='64 true false\ntrue\ntrue\ntrue P-256\ntrue true\n',
challenge='Sign a message with ed25519.NewKeyFromSeed using a fixed 32-byte seed of zeros, then show that signing again gives the identical signature (Ed25519 is deterministic).',
solution=r'''package main

import (
    "bytes"
    "crypto/ed25519"
    "fmt"
)

func main() {
    priv := ed25519.NewKeyFromSeed(make([]byte, ed25519.SeedSize))
    a := ed25519.Sign(priv, []byte("same"))
    b := ed25519.Sign(priv, []byte("same"))
    fmt.Println(bytes.Equal(a, b), len(priv.Public().(ed25519.PublicKey)))
}
''',
solutionStdout='true 32\n',
question='Why should a signing function accept crypto.Signer instead of *ecdsa.PrivateKey?',
correct='Any key type, including keys held in hardware, can then be used',
wrong=['crypto.Signer is faster', 'ECDSA keys cannot sign directly'],
reasoning='Signer abstracts where and how the private key lives. TLS uses it so certificates can be backed by HSMs or cloud KMS.',
sourceURL=PKG+'crypto#Signer',
additionalReadings=[dict(title='crypto/ed25519', url=PKG+'crypto/ed25519', section='Sign'), dict(title='crypto/rsa', url=PKG+'crypto/rsa', section='PSS')]),

dict(key='crypto-key-exchange', stage=STAGE, title='Key exchange: X25519 with crypto/ecdh and ML-KEM',
body=[
'Key exchange lets two parties agree a shared secret over an open channel. crypto/ecdh (Go 1.20) implements X25519 and the NIST curves: each side generates a key pair, sends its public key, and computes ECDH(own private, peer public), which yields the same secret on both sides.',
'Quantum computers would break elliptic-curve exchange, so crypto/mlkem (Go 1.24) provides ML-KEM, the NIST post-quantum key-encapsulation mechanism. The receiver publishes an encapsulation key; the sender calls Encapsulate to get a shared key plus a ciphertext; the receiver Decapsulates the ciphertext to recover the same key. TLS in Go combines both as the hybrid X25519MLKEM768 by default.',
'crypto/mlkem/mlkemtest exposes deterministic encapsulation from fixed randomness for known-answer tests; it must never be used in production. Always derive working keys from a shared secret with HKDF rather than using it directly.',
],
code=r'''package main

import (
    "bytes"
    "crypto/ecdh"
    "crypto/mlkem"
    "crypto/mlkem/mlkemtest"
    "fmt"
)

func main() {
    alice, _ := ecdh.X25519().GenerateKey(nil)
    bob, _ := ecdh.X25519().GenerateKey(nil)
    s1, _ := alice.ECDH(bob.PublicKey())
    s2, _ := bob.ECDH(alice.PublicKey())
    fmt.Println(len(s1), bytes.Equal(s1, s2))
    dk, _ := mlkem.GenerateKey768()
    ek := dk.EncapsulationKey()
    shared, ciphertext := ek.Encapsulate()
    recovered, err := dk.Decapsulate(ciphertext)
    fmt.Println(len(ek.Bytes()), len(ciphertext), bytes.Equal(shared, recovered), err)
    fixed := make([]byte, 32)
    k1, c1, _ := mlkemtest.Encapsulate768(ek, fixed)
    k2, c2, _ := mlkemtest.Encapsulate768(ek, fixed)
    fmt.Println(bytes.Equal(k1, k2) && bytes.Equal(c1, c2))
}
''',
expectedStdout='32 true\n1184 1088 true <nil>\ntrue\n',
challenge='Do an ECDH exchange on the P-256 curve instead of X25519 and print the shared-secret length and whether both sides agree.',
solution=r'''package main

import (
    "bytes"
    "crypto/ecdh"
    "fmt"
)

func main() {
    a, _ := ecdh.P256().GenerateKey(nil)
    b, _ := ecdh.P256().GenerateKey(nil)
    s1, _ := a.ECDH(b.PublicKey())
    s2, _ := b.ECDH(a.PublicKey())
    fmt.Println(len(s1), bytes.Equal(s1, s2))
}
''',
solutionStdout='32 true\n',
question='Why does Go\'s TLS use the hybrid X25519MLKEM768 by default?',
correct='It stays secure if either the classical or the post-quantum component is broken',
wrong=['ML-KEM alone is not standardised', 'X25519 is already broken'],
reasoning='Hybrids combine both secrets, defending against future quantum attacks without trusting the newer scheme alone.',
sourceURL=PKG+'crypto/mlkem',
additionalReadings=[dict(title='crypto/ecdh', url=PKG+'crypto/ecdh', section='X25519')]),

dict(key='crypto-post-quantum', stage=STAGE, title='Post-quantum signatures, HPKE and FIPS 140-3 mode',
body=[
'Go 1.27 adds crypto/mldsa, the NIST ML-DSA post-quantum signature scheme (FIPS 204), with three parameter sets: MLDSA44, MLDSA65 and MLDSA87. Keys implement crypto.Signer; Options.Context separates signatures made for different purposes. Signatures are larger than Ed25519 (2420 bytes for ML-DSA-44).',
'crypto/hpke implements Hybrid Public Key Encryption (RFC 9180): Seal encrypts to a recipient\'s public key by combining a KEM, a KDF and an AEAD; Open decrypts with the private key. With the MLKEM768X25519 KEM, the encryption is post-quantum hybrid. Encrypted Client Hello and MLS build on HPKE.',
'crypto/fips140 reports whether the program runs in FIPS 140-3 mode (GODEBUG=fips140=on), which restricts algorithms to approved ones. Version names the Go Cryptographic Module in use. Most programs never need it; regulated environments do.',
],
code=r'''package main

import (
    "crypto/fips140"
    "crypto/hpke"
    "crypto/mldsa"
    "fmt"
)

func main() {
    sk, _ := mldsa.GenerateKey(mldsa.MLDSA44())
    opts := &mldsa.Options{Context: "release-signing"}
    sig, err := sk.Sign(nil, []byte("v1.27.2"), opts)
    fmt.Println(len(sig), err)
    fmt.Println(mldsa.Verify(sk.PublicKey(), []byte("v1.27.2"), sig, opts) == nil)
    fmt.Println(mldsa.Verify(sk.PublicKey(), []byte("v1.27.2"), sig, &mldsa.Options{Context: "other"}) != nil)
    kem := hpke.MLKEM768X25519()
    priv, _ := kem.GenerateKey()
    ct, _ := hpke.Seal(priv.PublicKey(), hpke.HKDFSHA256(), hpke.AES256GCM(), []byte("app info"), []byte("hello, future"))
    pt, err := hpke.Open(priv, hpke.HKDFSHA256(), hpke.AES256GCM(), []byte("app info"), ct)
    fmt.Println(string(pt), err)
    fmt.Println(fips140.Enabled())
}
''',
expectedStdout='2420 <nil>\ntrue\ntrue\nhello, future <nil>\nfalse\n',
challenge='Show that hpke.Open fails when the info argument differs from the one used by Seal, using the DHKEM(X25519) KEM.',
solution=r'''package main

import (
    "crypto/ecdh"
    "crypto/hpke"
    "fmt"
)

func main() {
    kem := hpke.DHKEM(ecdh.X25519())
    priv, _ := kem.GenerateKey()
    ct, _ := hpke.Seal(priv.PublicKey(), hpke.HKDFSHA256(), hpke.ChaCha20Poly1305(), []byte("a"), []byte("msg"))
    _, err := hpke.Open(priv, hpke.HKDFSHA256(), hpke.ChaCha20Poly1305(), []byte("b"), ct)
    fmt.Println(err != nil)
}
''',
solutionStdout='true\n',
question='What does Options.Context do in ML-DSA?',
correct='Binds a signature to a purpose, so it does not verify under another context',
wrong=['Selects the parameter set', 'Adds a timestamp to the signature'],
reasoning='Domain separation prevents a signature produced for one protocol from being replayed in another.',
sourceURL=PKG+'crypto/mldsa',
additionalReadings=[dict(title='crypto/hpke', url=PKG+'crypto/hpke', section='Seal and Open'), dict(title='crypto/fips140', url=PKG+'crypto/fips140', section='Enabled')]),

dict(key='crypto-x509', stage=STAGE, title='Certificates with crypto/x509 and pkix names',
body=[
'An X.509 certificate binds a public key to a name, signed by an issuer. x509.CreateCertificate builds one from a template: subject (a pkix.Name with CommonName, Organization and so on), validity period, key usages, DNS names and the issuer. Encode it in PEM with pem.Encode for files.',
'x509.ParseCertificate decodes DER, and cert.Verify checks the signature chain up to roots in a CertPool, the validity period and the host name. Verification failures return typed errors such as x509.UnknownAuthorityError and x509.HostnameError.',
'crypto/x509/pkix holds the ASN.1 structures for names, extensions and revocation lists. Go 1.27 adds ML-DSA certificate support. For TLS, tls.Config consumes these certificates; for an internal CA, keep the root key offline.',
],
code=r'''package main

import (
    "crypto/ed25519"
    "crypto/x509"
    "crypto/x509/pkix"
    "encoding/pem"
    "errors"
    "fmt"
    "math/big"
    "time"
)

func main() {
    pub, priv, _ := ed25519.GenerateKey(nil)
    now := time.Now()
    tmpl := &x509.Certificate{
        SerialNumber:          big.NewInt(1),
        Subject:               pkix.Name{CommonName: "guide root", Organization: []string{"Gophers"}},
        NotBefore:             now.Add(-time.Hour),
        NotAfter:              now.Add(time.Hour),
        IsCA:                  true,
        BasicConstraintsValid: true,
        KeyUsage:              x509.KeyUsageCertSign | x509.KeyUsageDigitalSignature,
        DNSNames:              []string{"guide.test"},
    }
    der, err := x509.CreateCertificate(nil, tmpl, tmpl, pub, priv)
    fmt.Println(err)
    cert, _ := x509.ParseCertificate(der)
    fmt.Println(cert.Subject.String(), cert.SignatureAlgorithm)
    roots := x509.NewCertPool()
    roots.AddCert(cert)
    _, err = cert.Verify(x509.VerifyOptions{Roots: roots, DNSName: "guide.test"})
    fmt.Println(err)
    _, err = cert.Verify(x509.VerifyOptions{Roots: roots, DNSName: "evil.test"})
    var hostErr x509.HostnameError
    fmt.Println(errors.As(err, &hostErr))
    block := pem.EncodeToMemory(&pem.Block{Type: "CERTIFICATE", Bytes: der})
    fmt.Println(string(block[:27]))
}
''',
expectedStdout='<nil>\nCN=guide root,O=Gophers Ed25519\n<nil>\ntrue\n-----BEGIN CERTIFICATE-----\n',
challenge='Verify the self-signed certificate against an empty CertPool and print whether the error is an x509.UnknownAuthorityError.',
solution=r'''package main

import (
    "crypto/ed25519"
    "crypto/x509"
    "crypto/x509/pkix"
    "errors"
    "fmt"
    "math/big"
    "time"
)

func main() {
    pub, priv, _ := ed25519.GenerateKey(nil)
    tmpl := &x509.Certificate{SerialNumber: big.NewInt(1), Subject: pkix.Name{CommonName: "x"},
        NotBefore: time.Now().Add(-time.Hour), NotAfter: time.Now().Add(time.Hour)}
    der, _ := x509.CreateCertificate(nil, tmpl, tmpl, pub, priv)
    cert, _ := x509.ParseCertificate(der)
    _, err := cert.Verify(x509.VerifyOptions{Roots: x509.NewCertPool()})
    var unknown x509.UnknownAuthorityError
    fmt.Println(errors.As(err, &unknown))
}
''',
solutionStdout='true\n',
question='What does cert.Verify check besides the signature chain?',
correct='Validity period, key usage constraints and, if given, the DNS name',
wrong=['Only that the certificate parses', 'Whether the private key is still secret'],
reasoning='Verify builds a chain to a trusted root and applies the standard constraints. Revocation checking is not included.',
sourceURL=PKG+'crypto/x509',
additionalReadings=[dict(title='crypto/x509/pkix', url=PKG+'crypto/x509/pkix', section='Name')]),

dict(key='cryptotest-project', stage=STAGE, title='Deterministic cryptographic tests with testing/cryptotest',
body=[
'Cryptographic code is hard to test because keys and nonces are random. testing/cryptotest.SetGlobalRandom(t, seed) makes crypto/rand, and every implicit random source in the crypto packages, deterministic for the duration of one test. The same seed then produces the same keys and ciphertexts.',
'Because it changes process-wide state, it cannot be used with t.Parallel. The exact bytes produced for a seed are not a stable API across Go releases, so tests should compare two runs within the same test, or check properties, rather than hard-coding outputs.',
'This project tests a token-signing package: one test proves determinism under a fixed seed, another proves that different seeds give different keys, and the practice adds a tampering test.',
],
code='', expectedStdout='', solution='', solutionStdout='',
project=[
f('go.mod', 'module example.com/token\n\ngo 1.27\n'),
f('token.go', r'''// Package token issues signed tokens.
package token

import (
    "crypto/ed25519"
    "encoding/base64"
    "errors"
    "strings"
)

// Issuer signs tokens with a fresh Ed25519 key.
type Issuer struct {
    pub  ed25519.PublicKey
    priv ed25519.PrivateKey
}

// NewIssuer creates an issuer with a key from crypto/rand.
func NewIssuer() (*Issuer, error) {
    pub, priv, err := ed25519.GenerateKey(nil)
    if err != nil {
        return nil, err
    }
    return &Issuer{pub, priv}, nil
}

// Issue returns payload.signature in base64url.
func (i *Issuer) Issue(payload string) string {
    sig := ed25519.Sign(i.priv, []byte(payload))
    return payload + "." + base64.RawURLEncoding.EncodeToString(sig)
}

// Check returns the payload of a valid token.
func (i *Issuer) Check(tok string) (string, error) {
    payload, sig64, ok := strings.Cut(tok, ".")
    if !ok {
        return "", errors.New("malformed token")
    }
    sig, err := base64.RawURLEncoding.DecodeString(sig64)
    if err != nil || !ed25519.Verify(i.pub, []byte(payload), sig) {
        return "", errors.New("invalid signature")
    }
    return payload, nil
}
'''),
f('token_test.go', r'''package token

import (
    "testing"
    "testing/cryptotest"
)

func TestDeterministicUnderSeed(t *testing.T) {
    cryptotest.SetGlobalRandom(t, 42)
    a, _ := NewIssuer()
    cryptotest.SetGlobalRandom(t, 42)
    b, _ := NewIssuer()
    if a.Issue("user=ada") != b.Issue("user=ada") {
        t.Fatal("same seed produced different keys")
    }
    cryptotest.SetGlobalRandom(t, 7)
    c, _ := NewIssuer()
    if c.Issue("user=ada") == a.Issue("user=ada") {
        t.Fatal("different seeds produced the same key")
    }
}

func TestRoundTrip(t *testing.T) {
    iss, _ := NewIssuer()
    got, err := iss.Check(iss.Issue("user=bo"))
    if err != nil || got != "user=bo" {
        t.Fatalf("Check = %q, %v", got, err)
    }
}
'''),
],
projectSolutionFiles=[f('tamper_test.go', r'''package token

import "testing"

func TestTamperedPayloadRejected(t *testing.T) {
    iss, _ := NewIssuer()
    tok := iss.Issue("role=user")
    forged := "role=admin" + tok[len("role=user"):]
    if _, err := iss.Check(forged); err == nil {
        t.Fatal("forged token accepted")
    }
    if _, err := iss.Check("no-dot"); err == nil {
        t.Fatal("malformed token accepted")
    }
}
''')],
projectInstructions='Go 1.27 (testing/cryptotest), standard library only. Run:\ngo test -v ./...\nThe determinism test shows that SetGlobalRandom fixes crypto/rand within a test.\nPractice: add a test proving that changing the payload invalidates the signature and that malformed tokens are rejected. Add tamper_test.go from the worked answer.',
projectChecks=[
dict(name='seeded determinism and round trip', args=['test', '-count=1', '-v', './...'], outputContains=['--- PASS: TestDeterministicUnderSeed', '--- PASS: TestRoundTrip']),
dict(name='skipping verification is caught by the answer test', args=['test', '-count=1', './...'], useSolution=True, exit=1,
     mutations=[dict(path='token.go', find='if err != nil || !ed25519.Verify(i.pub, []byte(payload), sig) {', replace='if err != nil || len(sig) == 0 {')], outputContains=['forged token accepted']),
dict(name='answer tamper test', args=['test', '-count=1', '-v', '-run', 'TestTampered', './...'], useSolution=True, outputContains=['--- PASS: TestTamperedPayloadRejected']),
],
challenge='Add a test proving that a token whose payload was changed is rejected, and that a token without a dot is malformed.',
question='Why can SetGlobalRandom not be used in a parallel test?',
correct='It replaces the process-wide cryptographic randomness source',
wrong=['Parallel tests cannot import crypto packages', 'It only works in benchmarks'],
reasoning='Another test running concurrently would also draw from the deterministic source, breaking both tests\' assumptions.',
sourceURL=PKG+'testing/cryptotest'),
]
