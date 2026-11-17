using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Runtime.CompilerServices;

namespace CartelaNativeKernel
{
    internal struct Mask128
    {
        public ulong Lo;
        public ulong Hi;

        [MethodImpl(MethodImplOptions.AggressiveInlining)]
        public void SetBit(int num1Based)
        {
            int bit = num1Based - 1;
            if (bit < 64) Lo |= (1UL << bit);
            else Hi |= (1UL << (bit - 64));
        }

        [MethodImpl(MethodImplOptions.AggressiveInlining)]
        public bool ContainsAll(Mask128 target)
        {
            return (Lo & target.Lo) == target.Lo && (Hi & target.Hi) == target.Hi;
        }

        [MethodImpl(MethodImplOptions.AggressiveInlining)]
        public int IntersectPopCount(Mask128 other)
        {
            return Program.PopCount64(Lo & other.Lo) + Program.PopCount64(Hi & other.Hi);
        }
    }

    internal static unsafe class Program
    {
        [MethodImpl(MethodImplOptions.AggressiveInlining)]
        internal static int PopCount64(ulong x)
        {
            x = x - ((x >> 1) & 0x5555555555555555UL);
            x = (x & 0x3333333333333333UL) + ((x >> 2) & 0x3333333333333333UL);
            x = (x + (x >> 4)) & 0x0F0F0F0F0F0F0F0FUL;
            return (int)((x * 0x0101010101010101UL) >> 56);
        }

        private static long Binomial(int n, int k)
        {
            if (k < 0 || k > n) return 0;
            if (k == 0 || k == n) return 1;
            if (k > n - k) k = n - k;
            long res = 1;
            for (int i = 1; i <= k; i++)
            {
                res = res * (n - k + i) / i;
            }
            return res;
        }

        private static void GenerateCombinations(int[] pool, int k, Mask128[] output)
        {
            int n = pool.Length;
            int* idx = stackalloc int[k];
            for (int i = 0; i < k; i++) idx[i] = i;

            int outPos = 0;
            while (true)
            {
                Mask128 mask = new Mask128();
                for (int i = 0; i < k; i++)
                {
                    mask.SetBit(pool[idx[i]]);
                }
                output[outPos++] = mask;

                int p = k - 1;
                while (p >= 0 && idx[p] == n - k + p) p--;
                if (p < 0) break;

                idx[p]++;
                for (int j = p + 1; j < k; j++)
                {
                    idx[j] = idx[j - 1] + 1;
                }
            }
        }

        private static int RunCover(int t, int k, int[] pool)
        {
            int v = pool.Length;
            long numBlocks = Binomial(v, k);
            long numTargets = Binomial(v, t);
            if (numBlocks <= 0 || numTargets <= 0 || numBlocks > int.MaxValue || numTargets > int.MaxValue)
            {
                return 2;
            }

            Mask128[] blocks = new Mask128[numBlocks];
            Mask128[] targets = new Mask128[numTargets];
            GenerateCombinations(pool, k, blocks);
            GenerateCombinations(pool, t, targets);

            bool[] usedBlock = new bool[numBlocks];
            var selectedIndices = new List<int>();
            int remaining = (int)numTargets;

            fixed (Mask128* pBlocks = blocks)
            fixed (Mask128* pTargets = targets)
            {
                while (remaining > 0)
                {
                    int bestIdx = -1;
                    int bestCount = 0;

                    for (int b = 0; b < (int)numBlocks; b++)
                    {
                        if (usedBlock[b]) continue;
                        Mask128 bMask = pBlocks[b];
                        int hits = 0;
                        for (int i = 0; i < remaining; i++)
                        {
                            if (bMask.ContainsAll(pTargets[i])) hits++;
                        }
                        if (hits > bestCount)
                        {
                            bestCount = hits;
                            bestIdx = b;
                            if (bestCount == remaining) break;
                        }
                    }

                    if (bestIdx < 0 || bestCount == 0) break;

                    usedBlock[bestIdx] = true;
                    selectedIndices.Add(bestIdx);
                    Mask128 chosen = pBlocks[bestIdx];

                    int writeIdx = 0;
                    for (int i = 0; i < remaining; i++)
                    {
                        if (!chosen.ContainsAll(pTargets[i]))
                        {
                            pTargets[writeIdx++] = pTargets[i];
                        }
                    }
                    remaining = writeIdx;
                }

                // Regenerate targets for redundancy pruning & 2-for-1 local reduction
                GenerateCombinations(pool, t, targets);
                int totalT = (int)numTargets;

                for (int s = selectedIndices.Count - 1; s >= 0; s--)
                {
                    int candidateBlock = selectedIndices[s];
                    bool redundant = true;
                    for (int ti = 0; ti < totalT; ti++)
                    {
                        Mask128 tm = pTargets[ti];
                        if (!pBlocks[candidateBlock].ContainsAll(tm)) continue;
                        bool coveredElsewhere = false;
                        for (int o = 0; o < selectedIndices.Count; o++)
                        {
                            if (o == s) continue;
                            if (pBlocks[selectedIndices[o]].ContainsAll(tm))
                            {
                                coveredElsewhere = true;
                                break;
                            }
                        }
                        if (!coveredElsewhere) { redundant = false; break; }
                    }
                    if (redundant) selectedIndices.RemoveAt(s);
                }

                if (selectedIndices.Count >= 3 && numBlocks <= 8500)
                {
                    bool improved = true;
                    while (improved)
                    {
                        improved = false;
                        for (int i = 0; i < selectedIndices.Count && !improved; i++)
                        {
                            for (int j = i + 1; j < selectedIndices.Count && !improved; j++)
                            {
                                var uncovered = new List<Mask128>();
                                for (int ti = 0; ti < totalT; ti++)
                                {
                                    Mask128 tm = pTargets[ti];
                                    bool cov = false;
                                    for (int o = 0; o < selectedIndices.Count; o++)
                                    {
                                        if (o == i || o == j) continue;
                                        if (pBlocks[selectedIndices[o]].ContainsAll(tm)) { cov = true; break; }
                                    }
                                    if (!cov) uncovered.Add(tm);
                                }
                                if (uncovered.Count == 0)
                                {
                                    selectedIndices.RemoveAt(j);
                                    selectedIndices.RemoveAt(i);
                                    improved = true;
                                    break;
                                }
                                for (int b = 0; b < (int)numBlocks; b++)
                                {
                                    Mask128 bm = pBlocks[b];
                                    bool coversAll = true;
                                    for (int u = 0; u < uncovered.Count; u++)
                                    {
                                        if (!bm.ContainsAll(uncovered[u])) { coversAll = false; break; }
                                    }
                                    if (coversAll)
                                    {
                                        selectedIndices[i] = b;
                                        selectedIndices.RemoveAt(j);
                                        improved = true;
                                        break;
                                    }
                                }
                            }
                        }
                    }
                }

                for (int s = 0; s < selectedIndices.Count; s++)
                {
                    Mask128 chosen = pBlocks[selectedIndices[s]];
                    int emitted = 0;
                    for (int num = 1; num <= 80; num++)
                    {
                        int bit = num - 1;
                        bool on = bit < 64 ? ((chosen.Lo & (1UL << bit)) != 0) : ((chosen.Hi & (1UL << (bit - 64))) != 0);
                        if (on)
                        {
                            if (emitted > 0) Console.Write(',');
                            Console.Write(num);
                            emitted++;
                        }
                    }
                    Console.WriteLine();
                }
            }
            return 0;
        }

        private static int RunBacktest(string jsonPath, Mask128 gameMask)
        {
            if (!File.Exists(jsonPath)) return 3;
            string raw = File.ReadAllText(jsonPath);
            var masksList = new List<Mask128>(4096);
            Mask128 curMask = new Mask128();
            int curNum = 0;
            int count = 0;
            bool inNum = false;

            for (int i = 0; i < raw.Length; i++)
            {
                char c = raw[i];
                if (c >= '0' && c <= '9')
                {
                    curNum = curNum * 10 + (c - '0');
                    inNum = true;
                }
                else if (inNum)
                {
                    if (curNum >= 1 && curNum <= 60)
                    {
                        curMask.SetBit(curNum);
                        count++;
                        if (count == 6)
                        {
                            masksList.Add(curMask);
                            curMask = new Mask128();
                            count = 0;
                        }
                    }
                    curNum = 0;
                    inNum = false;
                }
            }

            Mask128[] masks = masksList.ToArray();
            int n = masks.Length;
            int quadras = 0, quinas = 0, senas = 0;
            var hitsList = new List<string>();

            fixed (Mask128* pBase = masks)
            {
                for (int i = 0; i < n; i++)
                {
                    int hits = pBase[i].IntersectPopCount(gameMask);
                    if (hits >= 4)
                    {
                        if (hits == 4) quadras++;
                        else if (hits == 5) quinas++;
                        else senas++;
                        hitsList.Add((i + 1) + ":" + hits);
                    }
                }
            }

            Console.WriteLine(string.Format("{0};{1};{2};{3};{4}", n, quadras, quinas, senas, string.Join(",", hitsList)));
            return 0;
        }

        private static int RunMonteCarlo(long draws, Mask128 gameMask, int maxNum, int k)
        {
            int* pool = stackalloc int[maxNum];
            for (int i = 0; i < maxNum; i++) pool[i] = i + 1;

            ulong rng = (ulong)DateTime.UtcNow.Ticks ^ 0x9E3779B97F4A7C15UL;
            if (rng == 0) rng = 0x9E3779B97F4A7C15UL;

            long tier3 = 0, tier4 = 0, tier5 = 0, tier6 = 0;
            var sw = System.Diagnostics.Stopwatch.StartNew();

            for (long d = 0; d < draws; d++)
            {
                Mask128 drawMask = new Mask128();
                for (int i = 0; i < k; i++)
                {
                    rng ^= rng >> 12;
                    rng ^= rng << 25;
                    rng ^= rng >> 27;
                    ulong r = rng * 0x2545F4914F6CDD1DUL;
                    int j = i + (int)(r % (ulong)(maxNum - i));
                    int tmp = pool[i];
                    pool[i] = pool[j];
                    pool[j] = tmp;
                    drawMask.SetBit(pool[i]);
                }

                int hits = drawMask.IntersectPopCount(gameMask);
                if (hits >= 3)
                {
                    if (hits == 3) tier3++;
                    else if (hits == 4) tier4++;
                    else if (hits == 5) tier5++;
                    else tier6++;
                }
            }
            sw.Stop();

            Console.WriteLine(string.Format(
                CultureInfo.InvariantCulture,
                "{0};{1};{2};{3};{4};{5:0.00}",
                draws, tier3, tier4, tier5, tier6, sw.Elapsed.TotalMilliseconds));
            return 0;
        }

        private static int[] ParsePool(string csv)
        {
            string[] parts = csv.Split(new[] { ',' }, StringSplitOptions.RemoveEmptyEntries);
            int[] pool = new int[parts.Length];
            for (int i = 0; i < parts.Length; i++)
            {
                pool[i] = int.Parse(parts[i].Trim());
            }
            Array.Sort(pool);
            return pool;
        }

        private static int Main(string[] args)
        {
            if (args.Length < 3) return 1;
            string mode = args[0];
            if (mode == "cover")
            {
                int t = int.Parse(args[1]);
                int[] pool = ParsePool(args[2]);
                int k = args.Length >= 4 ? int.Parse(args[3]) : 6;
                return RunCover(t, k, pool);
            }
            if (mode == "backtest" || mode == "montecarlo")
            {
                int[] nums = ParsePool(args[2]);
                Mask128 mask = new Mask128();
                for (int i = 0; i < nums.Length; i++)
                {
                    if (nums[i] >= 1 && nums[i] <= 80) mask.SetBit(nums[i]);
                }
                if (mode == "backtest") return RunBacktest(args[1], mask);
                int maxNum = args.Length >= 4 ? int.Parse(args[3]) : 60;
                int k = args.Length >= 5 ? int.Parse(args[4]) : 6;
                return RunMonteCarlo(long.Parse(args[1]), mask, maxNum, k);
            }
            return 1;
        }
    }
}
