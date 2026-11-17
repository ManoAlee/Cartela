using System;
using System.Collections.Generic;
using System.IO;
using System.Runtime.CompilerServices;

namespace CartelaNativeKernel
{
    internal static unsafe class Program
    {
        [MethodImpl(MethodImplOptions.AggressiveInlining)]
        private static int PopCount64(ulong x)
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

        private static void GenerateCombinations(int[] pool, int k, ulong[] output)
        {
            int n = pool.Length;
            int* idx = stackalloc int[k];
            for (int i = 0; i < k; i++) idx[i] = i;

            int outPos = 0;
            while (true)
            {
                ulong mask = 0;
                for (int i = 0; i < k; i++)
                {
                    mask |= (1UL << (pool[idx[i]] - 1));
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

        private static int RunCover(int t, int[] pool)
        {
            int v = pool.Length;
            long numBlocks = Binomial(v, 6);
            long numTargets = Binomial(v, t);
            if (numBlocks <= 0 || numTargets <= 0 || numBlocks > int.MaxValue || numTargets > int.MaxValue)
            {
                return 2;
            }

            ulong[] blocks = new ulong[numBlocks];
            ulong[] targets = new ulong[numTargets];
            GenerateCombinations(pool, 6, blocks);
            GenerateCombinations(pool, t, targets);

            bool[] usedBlock = new bool[numBlocks];
            int remaining = (int)numTargets;

            fixed (ulong* pBlocks = blocks)
            fixed (ulong* pTargets = targets)
            {
                while (remaining > 0)
                {
                    int bestIdx = -1;
                    int bestCount = 0;

                    for (int b = 0; b < (int)numBlocks; b++)
                    {
                        if (usedBlock[b]) continue;
                        ulong bMask = pBlocks[b];
                        int hits = 0;
                        for (int i = 0; i < remaining; i++)
                        {
                            ulong tMask = pTargets[i];
                            if ((bMask & tMask) == tMask) hits++;
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
                    ulong chosen = pBlocks[bestIdx];

                    // Emit sorted dezenas for chosen mask
                    int emitted = 0;
                    for (int bit = 0; bit < 60; bit++)
                    {
                        if ((chosen & (1UL << bit)) != 0)
                        {
                            if (emitted > 0) Console.Write(',');
                            Console.Write(bit + 1);
                            emitted++;
                        }
                    }
                    Console.WriteLine();

                    // Compact uncovered targets in-place (O(remaining))
                    int writeIdx = 0;
                    for (int i = 0; i < remaining; i++)
                    {
                        ulong tMask = pTargets[i];
                        if ((chosen & tMask) != tMask)
                        {
                            pTargets[writeIdx++] = tMask;
                        }
                    }
                    remaining = writeIdx;
                }
            }
            return 0;
        }

        private static int RunBacktest(string jsonPath, ulong gameMask)
        {
            if (!File.Exists(jsonPath)) return 3;
            string raw = File.ReadAllText(jsonPath);
            var masksList = new List<ulong>(4096);
            ulong curMask = 0;
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
                        curMask |= (1UL << (curNum - 1));
                        count++;
                        if (count == 6)
                        {
                            masksList.Add(curMask);
                            curMask = 0;
                            count = 0;
                        }
                    }
                    curNum = 0;
                    inNum = false;
                }
            }

            ulong[] masks = masksList.ToArray();
            int n = masks.Length;
            int quadras = 0, quinas = 0, senas = 0;
            var hitsList = new List<string>();

            fixed (ulong* pBase = masks)
            {
                for (int i = 0; i < n; i++)
                {
                    int hits = PopCount64(pBase[i] & gameMask);
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
                return RunCover(t, pool);
            }
            if (mode == "backtest")
            {
                string jsonPath = args[1];
                int[] nums = ParsePool(args[2]);
                ulong mask = 0;
                for (int i = 0; i < nums.Length; i++)
                {
                    if (nums[i] >= 1 && nums[i] <= 60) mask |= (1UL << (nums[i] - 1));
                }
                return RunBacktest(jsonPath, mask);
            }
            return 1;
        }
    }
}
